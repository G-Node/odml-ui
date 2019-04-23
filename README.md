[![Build Status](https://travis-ci.org/G-Node/odml-ui.svg?branch=master)](https://travis-ci.org/G-Node/odml-ui)
[![PyPI version](https://img.shields.io/pypi/v/odml-ui.svg)](https://pypi.org/project/odML-UI/)


# odML Editor

The odML-Editor is a standalone GUI application used for working with the odML Documents. 
The Python odML library is available on [GitHub](https://github.com/G-Node/python-odml).
If you are not familiar with the version control system **git**, but still want to use it, 
have a look at the documentation available on the [git-scm website](https://git-scm.com/).

## Breaking changes

odML Version 1.4 introduced breaking format and API changes compared to the previous
versions of odML. Files saved in a previous format version can be automatically
converted into the new format via "File - Import". The import will create a new file
and will not overwrite the original file.

Be aware that the value dtype `binary` has been removed. Incorporating binary
data into odML files is discouraged, provide references to the original files using the
`URL` dtype instead.

For details regarding the introduced changes please check the [github release notes](
https://github.com/G-Node/odml-ui/releases).


## Release Versions

All released versions are distributed via the [Python Package Index](
https://pypi.org/project/odML-UI) and can be installed using `pip`:

    pip install odml-ui

Once installed, the program can be activated via the command line:

    odmlui

Note: It might be required to install the external GTK3 dependencies first.


## Dependencies

The odML-Editor makes use of the Gtk 3+ library for the GUI, and the 
`python-odml` library. The following dependencies need to be installed 
for the odML-Editor.

* Python 2.7+ or Python 3.4+
* odml v1.4  `(pip install odml)`


### For Ubuntu-based distributions

* `sudo apt-get install libgtk-3-0`
* `sudo apt-get install gobject-introspection`
* For Python 3, `sudo apt-get install python3-gi`
* For Python 2, `sudo apt-get install python-gi`


### For Fedora-based distributions

* `sudo dnf install gtk3`
* `sudo dnf install pygobject3`
* For Python 3, `sudo dnf install python3-gobject`
* For Python 2, `sudo dnf install python-gobject`


### Anaconda Dependencies

Anaconda environments require only the following packages before installing the odML-Editor:

* Python 2.7+ or Python 3.4+.
* Install the following packages in the following order:

        conda install -c pkgw/label/superseded gtk3
        conda install -c conda-forge pygobject
        conda install -c conda-forge gdk-pixbuf
        conda install -c pkgw-forge adwaita-icon-theme

NOTE: These packages currently only work on Linux out of the box!

The macOS installation of these 3rd party dependencies contain a bug which causes
the opening of any window selecting files to crash the application.

If you still want to use odmlui with conda on macOS, you currently need to
apply a manual fix at the start of your session in your active conda environment
to avert this crash:

`export GSETTINGS_SCHEMA_DIR=$CONDA_PREFIX/share/glib-2.0/schemas`

You can also add scripts to your conda environment that always automatically sets up the
required environment variable at the start of a conda session as described in the 
[conda documentation](
https://conda.io/docs/user-guide/tasks/manage-environments.html#macos-linux-save-env-variables).


### macOS using homebrew

For Python 2 (Python 3)

* `brew install gtk+ (gtk+3)`
* `brew install pygobject (pygobject3)`
* `brew install gnome-icon-theme`
* `brew install gobject-introspection`


### Windows with Anaconda

#### Dependencies

* [PyGObject for Windows](
   https://sourceforge.net/projects/pygobjectwin32/files) (tested with 3.24.1rev1)
* Python 2.7+
* odml v1.4+ `(pip install odml)`


#### Installation

* Install Anaconda
* Create a new environment with Python 2.7+
* Install [PyGObject](
  https://pygobject.readthedocs.io/en/latest/getting_started.html)
  for Windows - base package and GTK+ 3.18.9 package

Select portable Python installation -> add path to virtual env Python default:
C:\Users\userName\Anacaonda\envs\nameOfEnv\

* Start Anaconda prompt
* install odml `(pip install odml)`
* install odml-ui `(python setup.py install)`
* run with `(odmlui)`

#### Windows Warning

Windows of odml-ui cannot be moved (only maximized) - movement or resize of the windows
crashes the application.


# Installation from source

The most straightforward way to get to the odML-Editor source from
the command line is to use git and clone the repository from GitHub
into your directory of choice:

    cd /home/usr/toolbox/
    git clone https://github.com/G-Node/odml-ui.git

If you don't want to use git, download the ZIP file also provided on
GitHub to your computer (e.g. as above on your home directory under a "toolbox" folder).

To install the odML-Editor, enter the corresponding directory and run:

    cd /home/usr/toolbox/odml-ui/
    python setup.py install

Note: `pip install gi` will lead to a namespace conflict with the
required GObject introspection library.


# Documentation

More information about the project including related projects as well as tutorials and
examples can be found at our [odML project page](https://g-node.github.io/python-odml).


# Bugs & Questions

Should you find a behaviour that is likely a bug or feel there is something missing,
just create an issue over at the GitHub [odML-Editor issue tracker](
https://github.com/G-Node/odml-ui/issues).
