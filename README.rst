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

These dependencies currently only work on Linux, MacOS is not supported!

MacOS using homebrew:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For Python 2 (Python 3)

* :code:`brew install gtk+ (gtk+3)`
* :code:`brew install pygobject (pygobject3)`
* :code:`brew install gnome-icon-theme`
* :code:`brew install gobject-introspection`


Installation
------------

To download the odML-Editor, please either use git and clone the 
repository from GitHub::

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
odML related documentation can be found at the
`Python-odML <http://g-node.github.io/python-odml>`_ tutorial page.

Bugs & Questions
----------------

Should you find a behaviour that is likely a bug or feel there is something missing,
just create an issue over at the GitHub
`odML-Editor issue tracker <https://github.com/G-Node/odml-ui/issues>`_.
