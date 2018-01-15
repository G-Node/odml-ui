#!/usr/bin/env bash

echo Running install_conda.sh

set -e
set -v

if [[ "$TRAVIS_OS_NAME" = "linux" ]]; then
    sudo apt-get update
    MINICONDAVERSION="Linux"
else
    MINICONDAVERSION="MacOSX"
fi

if [[ "$CONDAPY" == "2.7" ]]; then
  wget https://repo.continuum.io/miniconda/Miniconda2-latest-$MINICONDAVERSION-x86_64.sh -O miniconda.sh;
else
  wget https://repo.continuum.io/miniconda/Miniconda3-latest-$MINICONDAVERSION-x86_64.sh -O miniconda.sh;
fi

bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda

# Useful for debugging any issues with conda
conda info -a
which python

if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
    conda create -q -n condaenv python=$CONDAPY
    source activate condaenv
    which python

    # Install supported gi dependencies as provided by the installation guide.
    # Currently there is still a dependency mixup for conda under osx.
    conda install -c pkgw/label/superseded gtk3
    conda install -c conda-forge pygobject
    conda install -c conda-forge gdk-pixbuf
    conda install -c pkgw-forge adwaita-icon-theme
else
    # Add custom channels
    conda config --add channels conda-forge
    conda config --add channels pkgw-forge
    # The used dependencies are not the one advertised via the readme
    # but can be more easily installed and suffice for the tests for now.
    conda create -q -n condaenv python=$CONDAPY gtk3 pygobject gdk-pixbuf adwaita-icon-theme
fi
