Intorduction
============

qlsync is a small GUI program for maintaining playlists and music
files on a portable device.  It uses Quod Libet to find playlists and
music files, but is otherwise independent.

Different transport protocols are supported to connect to your device:
filesystem (i.e. mounted mass storage devive), FTP, SFTP, and ADB
(Android Debug Bridge).  MTP will never be supported; it is utterly
hopeless.

Basic Usage
===========

The program enables you to specify the parameters (transport protocol,
music location, etc) for various devices.  These are saved in the file
~/.qlsync.  Note that any password you specify for e.g. ftp connection
will be stored in that file (in pickle format, so easily readable).
For this reason, permissions on that file are set to 600.  A future
version of this program may encrypt that file.  ;-)

The scan operation will scan both the Quod Libet library (for changed
playlists, etc), and your device.  A list of all playlists known to
Quod Libet is displayed, with those currently on the device ticked.

Simply tick/untick those playlists you do/don't want on your device,
and then hit sync.

qlsync will ignore any music files or playlists on your device which
aren't in the Quod Libet library.  It should delete files from your
device only in the following cases:

   1. You untick a playlist that was previously sync'd to the device.
      In this case the playlist and music it references will be
      deleted.  However, music files still referenced by another known
      playlist will be left on the device.

   2. You remove some music files from a playlist which is sync'd to
      the device.  In this case, the music files are deleted from the
      device, and the updated playlist file copied onto the device.

However, I strongly suggest you have backups for all music on your
device.  There are no guarantees in case something goes wrong.

Album-Oriented Sync
===================

Personally, I prefer to listen to complete albums, and I don't have
comprehensive playlists.  Since `qlsync` uses playlists to drive the
sync, this was a little annoying to say the least.  So the support
script `qlsync-create-album-playlists` will make a Quod Libet playlist
out of *every* album in your library.  It tries quite hard to separate
out multiple albums with the same name (e.g. "Greatest Hits"), but
gives up on incomplete or badly tagged albums.

Android Devices
===============
For Android devices, ADB is highly recommended.  You will need to
enable USB debugging (in developer options, which appear after you tap
repeatedly on About -> Software Information -> More -> Build Number).

Android devices are identified by serial number.  To find this, ensure
there is only one device plugged into your PC, then click the `Get
Device Serial` button.

As an example, on my HTC One S, I use these settings:

* music directory `/storage/sdcard0/Music`
* protocol `ADB`
* SD card root `/storage/sdcard0`

Note: the SD card root is required to trigger a rescan of uploaded music.

Additional Details
==================

Playlists are put in the subdirectory `qlsync` of the music folder on
the device.  However, they will not appear as actual playlists on the
device.  They are purely a mechanism for syncing music files.  (The
reason is, any real playlist on the device seem to live on after the
actual file is deleted, which is very annoying.)  Currently only M3U
format playlists are supported.  Playlists are copied or deleted after
all the music files.  This is because if the operation is cancelled,
qlsync forgets about files it had already copied or deleted.  So if
you restart the operation, it will start over, but end up with
everything copied or deleted.

So why does qlsync just look at playlists, rather than the actual
files on the device?  It's to support the two-stage process for
[loading music onto iPods](README.iPod.md).

Troublesome characters in filenames
===================================

Unfortunately `adb` can't deal with shell commands on files containing
& or ;.  I found no way around this.  Therefore, there is the facility
to rename all music files containing such characters, and edit all
playlists, using the program `qlsync-rename-troublesome-files`.  When
run with `-p`, it assumes *every* file it encounters is a playlist,
and edits it accordingly.  (Quod Libet playlists may not end in
`.m3u`.)  *WARNING*: Be careful to test its behaviour on a copy of
your files before running it, since it edits playlist files and
filenames in place.  Use `--dry-run` to see what it will do, and
ensure you have backups of files you don't want to risk losing.  You
have been warned!

Comments and requests for improvement welcome.

Simon Guest <simon.guest@tesujimath.org>
