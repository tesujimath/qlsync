# Copyright 2015 Simon Guest
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import os
import os.path

troublesome_map = { '&': 'and',
                    ';': '.',
                    '"': "'",
                    ':': '_',
                    '?': '.',
                    '|': '.',
                    }

def mapped_name(x):
    for bad in troublesome_map.keys():
        x = x.replace(bad, troublesome_map[bad])
    return x

def maybe_rename_file(root, x, dry_run):
    original_name = x
    x = mapped_name(x)
    if x != original_name:
        original_path = os.path.join(root, original_name)
        new_path = os.path.join(root, x)
        print("mv '%s' '%s'" % (original_path, new_path))
        if not dry_run:
            os.rename(original_path, new_path)
    if dry_run:
        return original_name
    else:
        return x

def maybe_edit_playlist(playlist_path, dry_run):
    changed = False
    playlist = []
    with open(playlist_path, 'r') as f:
        for old_name in f.readlines():
            old_name = old_name.rstrip('\n')
            new_name = mapped_name(old_name)
            playlist.append(new_name)
            if new_name != old_name:
                changed = True
                #print("%s -> %s in %s" % (old_name, new_name, playlist_path))
    if changed:
        print("edit %s" % playlist_path)
        if not dry_run:
            with open(playlist_path, 'w') as f:
                f.write("%s\n" % '\n'.join(playlist))

def rename_troublesome_files(topdir, all_playlists = False, dry_run = False):
    for root, dirs, files in os.walk(topdir, topdown = False):
        for x in dirs:
            maybe_rename_file(root, x, dry_run)
        for x in files:
            new_name = maybe_rename_file(root, x, dry_run)
            base, ext = os.path.splitext(new_name)
            if all_playlists or ext in [".m3u"]:
                maybe_edit_playlist(os.path.join(root, new_name), dry_run)
