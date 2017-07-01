#!/usr/bin/env python

import sys
import os
import glob

from distutils.core import setup

try:
    # only necessary for the windows build
    import py2exe
    kwargs.update({'console': ['odml-gui']})
except ImportError:
    py2exe = None

packages = [
    'odmlui',
    'odmlui.dnd',
    'odmlui.treemodel'
]

data_files = [('share/applications', ['odml.desktop']),
              ('share/pixmaps', glob.glob(os.path.join("images", "*")))
              ]

print("\n\nThe data files are :- \n")
print(data_files)
print('')

setup(name='odML-UI',
      version='1.3',
      description='open metadata Markup Language',
      author='Hagen Fritsch',
      author_email='fritsch+gnode@in.tum.de',
      url='http://www.g-node.org/projects/odml',
      packages=packages,
      options={
          'py2exe': {
              'packages': 'odml',
              'includes': 'cairo, pango, pangocairo, atk, gobject, gio, lxml, gzip, enum34',
          }
      },
      scripts=['odml-gui'],
      data_files=data_files
      )
