#!/bin/bash

# This script executes outside of the Python virtual environment,
# hence the packages installed will be system-wide, and not
# specific to the virtual environment.

set -e

echo "Running install_dependencies.sh"
echo $TRAVIS_PYTHON_VERSION

##########   Linux Build   ##########
if [[ $TRAVIS_OS_NAME == 'linux' ]]
then

    if [ ${TRAVIS_PYTHON_VERSION%.*} -eq 3 ]
    then
        packages='python3-gi'
    else
        packages='python-gi'
    fi

    sudo apt-get -qq update
    sudo apt-get install libffi-dev libglib2.0-dev
    sudo apt-get install gobject-introspection libgtk-3-dev
    sudo apt-get install ${packages}

####### OS X Build #######
else

    brew install gtk+
    brew install pygobject
    brew install gnome-icon-theme
    brew install gobject-introspection

fi

echo -e "\n ###########################################"
echo -e "  Installed all dependencies successfully !!"
echo -e " ###########################################"
