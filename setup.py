#!/usr/bin/env python
#
# distutils setup script for qlsync package

from distutils.core import setup

setup(name='qlsync',
      version='0.4',
      description='Sync utility for Quodlibet',
      author='Simon Guest',
      author_email='simon.guest@tesujimath.org',
      url='https://github.com/tesujimath/qlsync',
      packages=['qlsync'],
      scripts=['bin/qlsync', 'bin/qlsync-create-album-playlists', 'bin/qlsync-playlist-from-device', 'bin/qlsync-rename-troublesome-files'],
      license='GPLv2'
     )
