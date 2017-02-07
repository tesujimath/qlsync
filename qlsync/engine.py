# Copyright 2012 Simon Guest
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import pickle
import os
import os.path
import re
import shutil
import sys
import tempfile
import threading
import urllib
import urlparse

import quodlibet
import quodlibet.config
import quodlibet.formats
import quodlibet.library

from qlsync import *
from qlsync.shifters import ShifterError

def ascify(s):
    """Convert Unicode string to ASCII, discarding out-of-bounds characters."""
    return s.encode('ascii', 'ignore')

class Device(object):
    """Access to files on the device."""
    def __init__(self, name, musicdir, shifter, flatten = False):
        self.name = name
        self.musicdir = musicdir
        self.shifter = shifter
        self.flatten = flatten
        self.clear_non_persistent()

    def clear_non_persistent(self):
        """Clear non-persistent settings."""
        self.playlist_files = {}         # indexed by playlist_name, of set of music files
        self.all_songs = set()

    def __str__(self):
        return "Device(name=" + self.name + ",musicdir=" + self.musicdir + ",flatten=" + str(self.flatten) + \
               ",shifter=" + str(self.shifter) + ")"

    def playlist_dir(self):
        return os.path.join(self.musicdir, "qlsync")

    def musicfile_playlist_path(self, musicfile):
        """Return a relative path to music from playlist."""
        return os.path.join("..", musicfile) # because playlists are put into qlsync subdir

    def playlist_file(self, playlist_name):
        # We don't use a playlist file extension, as Android seems to
        # keep these playlists around after we have deleted them.
        # If you want actual playlists on your device, copy them by
        # hand - or use a future version of this program ;-)
        return os.path.join("qlsync", playlist_name + ".qls")

    def musicfile_actual_path(self, musicfile_in_playlist):
        """Given a musicfile in a device playlist, return the actual pathname.  The opposite of musicfile_playlist_path."""
        return os.path.normpath(os.path.join("qlsync", musicfile_in_playlist))

    def scan(self):
        """Get device storage space and all the playlists from the device, by looking in the playlist dir for qls files."""
        self.clear_non_persistent()
        self.shifter.open()
        usage = self.shifter.get_storage_space(self.musicdir)
        if self.shifter.path_exists(self.playlist_dir()):
            for f in self.shifter.ls(self.playlist_dir()):
                m = re.match(r'^(.*)\.qls', f)
                if m:
                    playlist_file = m.group(0)
                    playlist_name = m.group(1)
                    playlist_contents = self.shifter.readlines(os.path.join(self.playlist_dir(), playlist_file))
                    self.playlist_files[playlist_name] = set(playlist_contents)
                    self.all_songs.update(self.playlist_files[playlist_name])
        self.shifter.close()
        return usage

    # TODO remove obsolete:
    # def playlist_name(self, playlistfile):
    #     m = re.match(r'^(.*)\.m3u', f)
    #     if m:
    #         return m.group(1)
    #     else:
    #         return None

    def flush(self):
        """Clean up and flush out changes."""
        self.shifter.flush()
        self.shifter.close()

class Settings(object):
    def __init__(self, configFile = os.path.expanduser("~/.qlsync")):
        self.configFile = configFile
        self.devices = []              # list of Device
        self.currentDeviceIndex = None # index into devices
        self.load()

    def load(self):
        if os.path.exists(self.configFile):
            try:
                f = open(self.configFile, 'r')
                settings = pickle.load(f)
                currentDeviceIndex = pickle.load(f)
                # all OK, so store them
                self.devices = settings
                self.currentDeviceIndex = currentDeviceIndex
                f.close()
            except Exception as e:
                oldConfigFile = "%s.old" % self.configFile
                print("load settings failed: %s, renaming %s as %s" % (str(e), self.configFile, oldConfigFile))
                os.rename(self.configFile, oldConfigFile)
        self.clear_non_persistent()

    def save(self):
        self.clear_non_persistent()
        try:
            f = open(self.configFile, 'w')
            os.fchmod(f.fileno(), 0600)               # might have an FTP password here
            pickle.dump(self.devices, f)
            pickle.dump(self.currentDeviceIndex, f)
            f.close()
        except IOError as e:
            print "save settings failed: " + str(e)

    def clear_non_persistent(self):
        """Clear non-persistent settings."""
        for d in self.devices:
            d.clear_non_persistent()

    def store_device(self, device, deviceIndex):
        device_list_changed = False
        if deviceIndex == None:
            self.devices.append(device)
            deviceIndex = len(self.devices) - 1
            device_list_changed = True
        else:
            self.devices[deviceIndex] = device
        self.currentDeviceIndex = deviceIndex
        self.save()
        if device_list_changed:
            self.notify_device_list_changed()
        self.notify_current_device_changed()

    def delete_device(self, deviceIndex):
        del self.devices[deviceIndex]
        if self.currentDeviceIndex == None:
            pass
        elif len(self.devices) == 0:
            self.currentDeviceIndex == None
        elif self.currentDeviceIndex == deviceIndex:
            self.currentDeviceIndex = 0
        elif self.currentDeviceIndex > deviceIndex:
            self.currentDeviceIndex -= 1
        self.save()
        self.notify_current_device_changed()
        self.notify_device_list_changed()

    def watch_current_device(self, callback):
        self.current_device_callback = callback

    def notify_current_device_changed(self):
        if hasattr(self, 'current_device_callback'):
            self.current_device_callback()

    def watch_device_list(self, callback):
        self.device_list_callback = callback

    def notify_device_list_changed(self):
        if hasattr(self, 'device_list_callback'):
            self.device_list_callback()

def flattened_path(path):
    """Flatten a path, i.e. squash all directory names into a single filename."""
    dirname, flattened = os.path.split(path)
    while dirname != "" and dirname != "/":
        dirname, basename = os.path.split(dirname)
        flattened = basename + " - " + flattened
    return flattened

class M3UFile(object):
    """An m3u format playlist, written to a tempfile."""
    def __init__(self, filename, library):
        self.f = open(filename, "w")
        self.library = library

    def append(self, musicFile):
        self.f.write(musicFile + "\n")

    def close(self):
        self.f.close()

def tracknumber_as_int(song):
    tracknumber = song['tracknumber']
    slash_pos = tracknumber.find('/')
    if slash_pos >= 0:
        return int(tracknumber[:slash_pos])
    else:
        return int(tracknumber)

def discnumber_as_int(song):
    try:
        discnumber = int(song['discnumber'])
    except (KeyError, ValueError):
        discnumber = 1
    return discnumber

class Song(object):
    def __init__(self, dict):
        self.dict = dict

    def description(self):
        if self.dict.has_key("tracknumber"):
            tracknumber = "%s - " % self.dict.tracknumber
        else:
            tracknumber = ""
        if self.dict.has_key("title"):
            title = self.dict.title
        else:
            title = "<unknown>"
        return "%s%s" % (tracknumber, title)

class Album(object):
    def __init__(self, album_name, artist, tracks):
        self.artist = artist
        self.name = album_name
        self.songs = []
        self.complete = has_all_tracks(tracks)
        for track in sorted(tracks.keys()):
            self.songs.append(tracks[track])

    def description(self):
        return "%s - %s (%d %s%s)" % (self.artist,
                                     self.name, len(self.songs),
                                     "songs" if len(self.songs) > 1 else "song",
                                     "" if self.complete else ", incomplete")

def has_all_tracks(dict, min = 2):
    """Need at least min tracks."""
    has_all = sorted(dict.keys()) == list(range(1, 1 + len(dict.keys()))) and len(dict) >= min
    return has_all

def refine_album(composite_album):
    """May have to split an album up, e.g. Greatest Hits may be several albums rolled into one."""
    refined_albums = []
    component_albums = {}
    bad_album = False
    artist = None
    album_name = None
    track = None
    for song in composite_album.songs:
        try:
            artist = song['artist']
            album_name = song['album']
            track = tracknumber_as_int(song)
            # TODO remove
            if album_name == "Reel Chill - The Cinematic Chillout Album" and track == 1:
                print("%s - %d songs" % (album_name, len(composite_album.songs)))
        except KeyError:
            bad_album = True
        if not bad_album:
            if not component_albums.has_key(album_name):
                component_albums[album_name] = {}
            if not component_albums[album_name].has_key(artist):
                component_albums[album_name][artist] = {}
            component_albums[album_name][artist][track] = song
    if bad_album:
        component_albums = {}
        sys.stderr.write("Badly tagged album: %s - %s\n" % (str(artist), str(album_name)))
    for album_name in component_albums.keys():
        various_artists = {}
        for artist in component_albums[album_name].keys():
            # if we've got consecutive tracks, then make it a standalone album
            if has_all_tracks(component_albums[album_name][artist]):
                refined_albums.append(Album(album_name, artist, component_albums[album_name].pop(artist)))
                print("1 %s" % refined_albums[-1].description())
            else:
                # collect into various artists
                for track in component_albums[album_name][artist].keys():
                    various_artists[track] = component_albums[album_name][artist][track]
        # anything remaining may be a various artists album
        if len(various_artists) == 0:
            pass
        elif has_all_tracks(various_artists):
            refined_albums.append(Album(album_name, "Various", various_artists))
            print("2 %s" % refined_albums[-1].description())
        else:
            # find an artist for the incomplete album
            artist = None
            for track in range(1, 20):
                try:
                    artist = various_artists[track]['artist']
                except KeyError:
                    pass
                if artist is not None:
                    break
            if artist is None:
                artist = "Unknown"
            refined_albums.append(Album(album_name, artist, various_artists))
            print("3 %s" % refined_albums[-1].description())
            sys.stderr.write("Incomplete album: %s - %s - %s\n" % (artist, album_name, [track for track in sorted(various_artists.keys())]))
    return refined_albums

def album_name_and_artist(album):
    """If all songs in the album are by the same artist, that is it, else Various."""
    artist = None
    album_name = None
    for song in album.songs:
        if album_name is None:
            album_name = song['album']
        elif song['album'] != album_name:
            # this shouldn't happen, all should be the same
            raise KeyError
        if artist is None:
            artist = song['artist']
        elif song['artist'] != artist:
            artist = "Various"
    return album_name, artist

class Library(object):
    """Access to music files and playlists."""
    def __init__(self):
        quodlibet.config.init(quodlibet.const.CONFIG)
        quodlibet.formats.init()
        scanSettings = quodlibet.config.get("settings", "scan")
        self.musicdirs = scanSettings.split(":")
        self.playlist_dir = os.path.expanduser("~/.quodlibet/playlists")
        self.quodlibet_library = quodlibet.library.init(quodlibet.const.LIBRARY)

    def playlists(self):
        return sorted(os.listdir(self.playlist_dir))

    def relativise(self, abspath):
        """Return the path relative to a library root, or None."""
        relpath = None
        matchlen = 0
        for ldir in self.musicdirs:
            if abspath.startswith(ldir):
                # want longest match, so we pick correctly between say
                # /path/to/mp3 and /path/to/mp3-extra
                if relpath == None or len(ldir) > matchlen:
                    matchlen = len(ldir)
                    relpath = abspath[matchlen:].lstrip("/")
        return relpath

    def playlist_files(self, playlist):
        """Iterator for files in a playlist, which yields in pairs, (relpath, abspath)."""
        pf = open(os.path.join(self.playlist_dir, playlist))
        for line in pf:
            abspath = line.rstrip("\n")
            relpath = self.relativise(abspath)
            if relpath != None:
                yield(relpath, abspath)
        pf.close()

    def album_playlist(self, prefix, album_artist, album_name):
        playlist_file = "%s%s - %s" % (prefix, ascify(album_artist), ascify(album_name))
        return os.path.join(self.playlist_dir, urllib.quote(playlist_file, safe = "-"))

    def create_album_playlists(self, prefix = ""):
        """Create a playlist for each album in the library."""
        keys = self.quodlibet_library.albums.keys()
        for key in keys:
            album = self.quodlibet_library.albums[key]
            for refined_album in refine_album(album):
                with open(self.album_playlist(prefix, refined_album.artist, refined_album.name), 'w') as playlist:
                    for song in refined_album.songs:
                        playlist.write("%s\n" % song['~filename'])

class Syncer(object):
    """Playlist synchronizer.
Queue up file copies and deletions, ensuring not to delete files which are required.
Files are not copied if they are already in the device playlist.
"""
    def __init__(self):
        self.library = Library()
        self.tmpdir = tempfile.mkdtemp()
        self.scribe = None
        self.scan_library()
        self.device_storage = (None, None) # unknown

    def scan_library(self):
        """Scan for quodlibet playlists."""
        # Keep Quodlibet's encoded playlist names, as trying to store
        # decoded names is troublesome.
        self.playlists = self.library.playlists()
        self.playlist_names = []
        self.playlist_index_by_name = {}
        self.playlists_on_device = [False] * len(self.playlists) # array of boolean
        i = 0
        for playlist in self.playlists:
            playlist_name = urlparse.unquote(playlist)
            self.playlist_names.append(playlist_name)
            self.playlist_index_by_name[playlist] = i
            i += 1
        self.notify_playlists_changed()

    def scan_device(self, device):
        """Scan what is on the device."""
        usage = device.scan()
        for playlist_name in device.playlist_files.keys():
            if self.playlist_index_by_name.has_key(playlist_name):
                i = self.playlist_index_by_name[playlist_name]
                self.playlists_on_device[i] = True
        self.notify_playlists_on_device_changed()
        self.notify_device_storage_changed(usage)

    def get_device_storage(self):
        return self.device_storage

    def sync_device(self, device, playlists_wanted, label_callback, progress_callback):
        """Sync playlists, adding and deleting so that only playlists_wanted are present."""
        print "writing data to device (do not unplug) ..."
        self.scribe = Scribe(device, label_callback, progress_callback)
        for i in range(len(self.playlists)):
            if playlists_wanted[i]:
                # wanted playlist, ensure it and all songs are on device
                self.create_and_queue_playlist(self.playlists[i],
                                               self.playlists[i],
                                               device,
                                               self.scribe)
            elif self.playlists[i] in device.playlist_files.keys():
                # unwanted playlist on device, so delete
                self.delete_playlist(self.playlists[i], device, self.scribe)
        self.scribe.start()

    def cancel_sync(self):
        if self.scribe != None:
            self.scribe.cancel()

    def sync_device_completed(self, progress, device):
        print "waiting for scribe"
        self.scribe.join()
        self.scribe = None
        # update local state to reflect what we did.  This is non optimal, but works:
        self.scan_device(device)
        print "%d%% done, you may safely remove your device" % int(progress * 100)

    def cleanup(self):
        shutil.rmtree(self.tmpdir)

    def watch_playlists(self, callback):
        self.playlists_callback = callback

    def notify_playlists_changed(self):
        if hasattr(self, 'playlists_callback'):
            self.playlists_callback()

    def watch_playlists_on_device(self, callback):
        self.playlists_on_device_callback = callback

    def notify_playlists_on_device_changed(self):
        if hasattr(self, 'playlists_on_device_callback'):
            self.playlists_on_device_callback()

    def watch_device_storage(self, callback):
        self.device_storage_callback = callback

    def notify_device_storage_changed(self, usage):
        if hasattr(self, 'device_storage_callback'):
            self.device_storage_callback(usage)

    def create_and_queue_playlist(self, playlist, playlist_name, device, scribe):
        """Copy over any songs which have changed."""
        new_playlist = playlist_name not in device.playlist_files.keys()
        playlist_files = []

        # queue copies for new files
        for relpath,abspath in self.library.playlist_files(playlist):
            if device.flatten:
                devicepath = flattened_path(relpath)
            else:
                devicepath = relpath
            devicepath_in_playlist = device.musicfile_playlist_path(devicepath)
            playlist_files.append(devicepath_in_playlist)
            if devicepath_in_playlist not in device.all_songs:
                scribe.queue_copy(abspath, devicepath)

        # determine whether we need to copy playlist itself, and queue deletions for obsolete files
        if new_playlist:
            need_to_copy_playlist = True
        else:
            playlist_files_set = set(playlist_files)
            for musicfile in (device.playlist_files[playlist_name] - playlist_files_set):
                scribe.queue_delete(device.musicfile_actual_path(musicfile))
            need_to_copy_playlist = (playlist_files_set != device.playlist_files[playlist_name])

        # copy playlist file if required
        if need_to_copy_playlist:
            m3uFile = os.path.join(self.tmpdir, playlist + ".m3u")
            f = open(m3uFile, "w")
            f.write("\n".join(playlist_files))
            f.close
            scribe.queue_copy_playlist(m3uFile, device.playlist_file(playlist_name))

    def delete_playlist(self, playlist_name, device, scribe):
        for musicfile in device.playlist_files[playlist_name]:
            scribe.queue_delete(device.musicfile_actual_path(musicfile))
        scribe.queue_delete_playlist(device.playlist_file(playlist_name))


class Scribe(threading.Thread):
    """Deletes then copies data onto the device in a background thread.  Playlists are copied/deleted after their music files."""

    def __init__(self, device, label_callback, progress_callback):
        super(Scribe, self).__init__()
        self.device = device
        self.label_callback = label_callback
        self.progress_callback = progress_callback
        self.actions = []          # list of (src,dst), with src = None for deletions
        self.copies = []           # list of (src,dst)
        self.deletions = []        # list of dst
        self.deleteRequired = {}             # indexed by dst, of deleteRequired
        self.n_copies = 0
        self.n_deletions = 0
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def queue_copy(self, src, dst):
        print("queue_copy(%s, %s)" % (src, dst))
        self.n_copies += 1
        self.copies.append((src,dst))
        self.deleteRequired[dst] = False

    def queue_copy_playlist(self, src, dst):
        print("queue_copy_playlist(%s, %s)" % (src, dst))
        self.n_copies += 1
        self.copies.append((src,dst))

    def queue_delete(self, dst):
        print("queue_delete(%s)" % dst)
        if not self.deleteRequired.has_key(dst):
            self.deleteRequired[dst] = True
        self.n_deletions += 1
        self.deletions.append(dst)

    def queue_delete_playlist(self, dst):
        print("queue_delete_playlist(%s)" % dst)
        if not self.deleteRequired.has_key(dst):
            self.deleteRequired[dst] = True
        self.n_deletions += 1
        self.deletions.append(dst)

    def check_cancelled(self):
        if not self.cancelled:
            self.cancelled = self.cancel_event.wait(0)
        return self.cancelled

    def run(self):
        """Copy all wanted files, and delete unwanted."""
        self.cancelled = False
        progress = 0.0

        # let GUI know what we're up to
        self.label_callback(str(self.n_copies) + " files to copy and " + str(self.n_deletions) + " to delete")

        # go for it
        self.device.shifter.open()
        dstRoot = self.device.musicdir
        delDirs = {}
        i_copy = 0
        i_delete = 0
        # deletions
        for dst in self.deletions:
            if self.check_cancelled():
                break
            dstFile = os.path.join(dstRoot, dst)
            dstDir = os.path.dirname(dstFile)
            if self.deleteRequired.has_key(dst) and self.deleteRequired[dst]:
                i_delete += 1
                print "removefile", i_delete, "of", self.n_deletions, ": ", dstFile
                delDirs[dstDir] = True
                try:
                    self.device.shifter.removefile(dstFile)
                except ShifterError as e:
                    # we don't care if this fails
                    print "ignoring error", e
                    pass
                progress = i_delete * 1.0 / (self.n_copies + self.n_deletions)
                self.progress_callback(progress)
        for dstDir in delDirs.keys():
            if self.check_cancelled():
                break
            self.device.shifter.removedir_if_empty(dstDir)
        for src,dst in self.copies:
            if self.check_cancelled():
                break
            dstFile = os.path.join(dstRoot, dst)
            dstDir = os.path.dirname(dstFile)
            if src is not None:
                i_copy += 1
                print "uploadfile", i_copy, "of", self.n_copies, ": ", dstFile
                self.device.shifter.makedirs(dstDir)
                self.device.shifter.uploadfile(src, dstFile)
                progress = (self.n_deletions + i_copy) * 1.0 / (self.n_copies + self.n_deletions)
                self.progress_callback(progress)
        if not self.cancelled:
            progress = 1
        self.device.flush()
        self.progress_callback(progress, True) # complete
