#!/bin/bash

# This script executes outside of the virtual environment,
# hence the packages installed will be system-wide, and not 
# specifically in the virtual environment.

python --version
python3 --version

sudo apt-get -qq update
sudo apt-get install libffi-dev libglib2.0-0 libglib2.0-dev
sudo apt-get install gobject-introspection
sudo apt-get install python-gi python3-gi
sudo apt-get install gir1.2-glib-2.0 

python -c "import gi"
python -c "from gi import pygtkcompat"
python3 -c "import gi"
python3 -c "from gi import pygtkcompat"

echo -e "\n\n #########################################"
echo -e " Installed all dependencies successfully !!"
echo -e "\n #########################################"

