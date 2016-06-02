#!/bin/bash

# set up virtual environment
ROOT=$PWD

echo "setting up virtual env..."
virtualenv --python=$(which python3) --no-site-packages . >/dev/null
if [ $? -ne 0 ]; then
    exit 1
fi

# make the environment active
source bin/activate

# upgrade setuptools and pip
tools=(pip setuptools)
for pkg in ${tools[@]}; do
    echo "updating $pkg..."
    pip install -U $pkg >/dev/null
    if [ $? -ne 0 ]; then
        exit 1
    fi
done

# install packages listed in dependencies.txt
echo "installing requirements..."
pip install -r requirements.txt >/dev/null
if [ $? -ne 0 ]; then
    echo "installation failed"
    exit 1
fi

# compile and install matlib package
cd src/matlib
python setup.py install
cd $ROOT
