
import os
import sys

prefix = sys.prefix

pixmaps = prefix + '/share/pixmaps/'
applications = prefix + '/share/applications/'

img_files = os.listdir(os.path.abspath("images") )

# Check if image files exist in the system.
for i in img_files:
    if not os.path.isfile(pixmaps + i):
        print("Not found :- %s" % pixmaps + i)
        exit(1)

if not os.path.isfile(applications + 'odml.desktop'):
    print("Not found :- %s" % (applications + 'odml.desktop'))
    exit(1)

### If importing 'gi' works in a virtual environment, we can
### use the following method to check if 'Gtk' dependencies
### are installed properly. Till then, this check happens in 
### the main travis build file.

# try:
#     import gi
#     from gi.repository import Gtk
# except Exception as e:
#     print(e)
#     exit(1)

exit(0)
