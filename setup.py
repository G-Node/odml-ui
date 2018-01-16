#!/usr/bin/env python
import glob
import os

from odmlui.info import VERSION, AUTHOR, CONTACT, HOMEPAGE, CLASSIFIERS
# Use setuptools compulsorily, as the distutils doesn't work out well for the
# installation procedure. The 'install_requires' and 'data_files' have better
# support in setuptools.
from setuptools import setup

try:
    # only necessary for the windows build
    import py2exe
    kwargs.update({'console': ['odml-gui']})
except ImportError:
    py2exe = None


class PackageNotFoundError(Exception):
    pass


# Check required non-python dependencies for native install,
# Anaconda and virtualenv environments.
readme = "README.rst"
dep_str = "Non-Python dependency missing, please check the %s file." % readme
try:
    import gi
    import pygtkcompat
    pygtkcompat.enable()
    pygtkcompat.enable_gtk(version='3.0')
    import gtk
    import gobject
except (ImportError, ValueError) as err:
    err_str = ("\n  Error: %s\n\n  %s" % (err, dep_str))
    raise PackageNotFoundError(err_str)


with open(readme) as f:
    description_text = f.read()

packages = [
    'odmlui',
    'odmlui.dnd',
    'odmlui.treemodel'
]

install_req = ["odml>=1.3.3"]

data_files = [('share/pixmaps', glob.glob(os.path.join("images", "*"))),
              ('share/odmlui', ['LICENSE'])]

setup(name='odML-UI',
      version=VERSION,
      description='odML Editor',
      author=AUTHOR,
      author_email=CONTACT,
      url=HOMEPAGE,
      packages=packages,
      options={
          'py2exe': {
              'packages': 'odml',
              'includes': 'cairo, pango, pangocairo, atk, '
                          'gobject, gio, lxml, gzip, enum34',
          }
      },
      install_requires=install_req,
      entry_points={'gui_scripts': ['odmlui = odmlui.__main__:run []']},
      data_files=data_files,
      long_description=description_text,
      classifiers=CLASSIFIERS,
      license="BSD",
      test_suite='test'
      )
