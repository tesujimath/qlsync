#!/usr/bin/env python
#
# distutils setup script for qlsync package

from distutils.core import setup

setup(name='qlsync',
      version='0.2',
      description='Sync utility for Quodlibet',
      author='Simon Guest',
      author_email='simon.guest@tesujimath.org',
      url='http://code.google.com/p/qlsync/',
      packages=['qlsync'],
      scripts=['bin/qlsync', 'bin/qlsync-playlist-from-device'],
      license='GPLv2'
     )
