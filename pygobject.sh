#!/bin/bash

# PyCairo (1.13.0)
wget https://github.com/pygobject/pycairo/releases/download/v1.13.0/pycairo-1.13.0.tar.gz
tar -xf pycairo-1.13.0.tar.gz
cd pycairo-1.13.0
sudo python3 setup.py install
cd ..

# PyGObject (3.12.2)
wget https://download.gnome.org/sources/pygobject/3.12/pygobject-3.12.2.tar.xz
tar -xf pygobject-3.12.2.tar.xz
cd pygobject-3.12.2
./configure
make
sudo make install
cd ..

