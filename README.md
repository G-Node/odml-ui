odML Editor
=========================

The odML-Editor is a standalone GUI application used for working with the odML Documents. The Python odML library is available on [https://github.com/G-Node/python-odml](https://github.com/G-Node/python-odml).
If you are not familiar with the version control system **git**, but still want to use it, have a look at the documentaion available on the `git-scm website <https://git-scm.com/>`_. 

Dependencies
------------

The odML-Editor makes use of the Gtk library for the GUI, and the `python-odml` library. Following dependencies need to be installed for the odML-Editor.

* Python 2.7+ or Python 3.4+
* odml v1.3  `(pip install odml)`
* `libffi-dev`
* `libglib2.0-dev`
* `libglib2.0-dev`
* `gobject-introspection`
* `libgtk-3-dev`
* For Python 2, `python-gi` 
* For Python 3, `python3-gi` 


Installation
------------

To download the odML-Editor, please either use git and clone the 
repository from GitHub:

	$ cd /home/usr/toolbox/
	$ git clone https://github.com/G-Node/odml-ui.git

... or if you don't want to use git, download the ZIP file also provided on 
GitHub to your computer (e.g. as above on your home directory under a "toolbox" folder).

To install the odML editor, enter the corresponding directory and run::

	$ cd /home/usr/toolbox/odml-ui/
	$ python setup.py install


Documentation
-------------
[Python-odML](http://g-node.github.io/python-odml)

Bugs & Questions
----------------

Should you find a behaviour that is likely a bug, please file a bug report at 
[the github bug tracker](https://github.com/G-Node/odml-ui/issues).

If you have questions regarding the use of the library or the editor, ask
the question on [Stack Overflow](http://stackoverflow.com/), be sure to tag
it with `odml` and we'll do our best to quickly solve the problem.
