odML Editor
===========

The odML-Editor is a standalone GUI application used for working with the odML Documents. 
The Python odML library is available on `GitHub <https://github.com/G-Node/python-odml>`_.
If you are not familiar with the version control system **git**, but still want to use it, 
have a look at the documentation available on the `git-scm website <https://git-scm.com/>`_.

Breaking changes
----------------

odML Version 1.4 introduced breaking format and API changes compared to the previous
versions of odML. Files saved in a previous format version can be automatically
converted into the new format via "File - Import". The import will create a new file
and will not overwrite the original file.

Be aware that the value dtype :code:`binary` has been removed. Incorporating binary
data into odML files is discouraged, provide references to the original files using the
:code:`URL` dtype instead.

For details regarding the introduced changes please check the `github release notes
<https://github.com/G-Node/odml-ui/releases>`_.


Release Versions
----------------
All released versions are distributed via the `Python Package Index <https://pypi.org/project/odML-UI>`_ and can
be installed using :code:`pip`

    $ pip install odml-ui

Once installed, the program can be activated via the command line:

    $ odmlui

Note: It might be required to install the external GTK3 dependencies first.


Dependencies
------------

The odML-Editor makes use of the Gtk 3+ library for the GUI, and the :code:`python-odml` library.
Following dependencies need to be installed for the odML-Editor.

* Python 2.7+ or Python 3.4+
* odml v1.4  :code:`(pip install odml)`

For Ubuntu-based distributions:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* :code:`sudo apt-get install libgtk-3-0`
* :code:`sudo apt-get install gobject-introspection`
* For Python 3, :code:`sudo apt-get install python3-gi`
* For Python 2, :code:`sudo apt-get install python-gi`

For Fedora-based distributions:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* :code:`sudo dnf install gtk3`
* :code:`sudo dnf install pygobject3`
* For Python 3, :code:`sudo dnf install python3-gobject`
* For Python 2, :code:`sudo dnf install python-gobject`

Anaconda Dependencies
~~~~~~~~~~~~~~~~~~~~~

Anaconda environments require only the following packages before installing the odML-Editor: 

* Python 2.7+ or Python 3.4+.
* Install the following packages in the following order.::

    $ conda install -c pkgw/label/superseded gtk3
    $ conda install -c conda-forge pygobject
    $ conda install -c conda-forge gdk-pixbuf
    $ conda install -c pkgw-forge adwaita-icon-theme

NOTE: These packages currently only work on Linux out of the box!

The macOS installation of these 3rd party dependencies contain a bug which causes
the opening of any window selecting files to crash the application.

If you still want to use odmlui with conda on macOS, you currently need to
apply a manual fix at the start of your session in your active conda environment
to avert this crash:

:code:`export GSETTINGS_SCHEMA_DIR=$CONDA_PREFIX/share/glib-2.0/schemas`

You can also add scripts to your conda environment that always automatically sets up the
required environment variable at the start of a conda session as described in the `conda documentation
<https://conda.io/docs/user-guide/tasks/manage-environments.html#macos-linux-save-env-variables>`_.


macOS using homebrew:
~~~~~~~~~~~~~~~~~~~~~
For Python 2 (Python 3)

* :code:`brew install gtk+ (gtk+3)`
* :code:`brew install pygobject (pygobject3)`
* :code:`brew install gnome-icon-theme`
* :code:`brew install gobject-introspection`


Installation from source
------------------------

The most straightforward way to get to the odML-Editor source from
the command line is to use git and clone the repository from GitHub
into your directory of choice::

  $ cd /home/usr/toolbox/
  $ git clone https://github.com/G-Node/odml-ui.git

If you don't want to use git, download the ZIP file also provided on
GitHub to your computer (e.g. as above on your home directory under a "toolbox" folder).

To install the odML-Editor, enter the corresponding directory and run::

  $ cd /home/usr/toolbox/odml-ui/
  $ python setup.py install

Note: :code:`pip install gi` will lead to a namespace conflict with the
required GObject introspection library.


Documentation
-------------

More information about the project including related projects as well as tutorials and
examples can be found at our `odML project page <https://g-node.github.io/python-odml>`_


Bugs & Questions
----------------

Should you find a behaviour that is likely a bug or feel there is something missing,
just create an issue over at the GitHub
`odML-Editor issue tracker <https://github.com/G-Node/odml-ui/issues>`_.
