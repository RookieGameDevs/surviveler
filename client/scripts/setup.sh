#!/bin/bash

# set up virtual environment
echo "setting up virtual env..."
virtualenv --python=$(which python3) --no-site-packages . >/dev/null
if [ $? -ne 0 ]; then
    exit
fi

# make the environment active
source bin/activate

# upgrade setuptools and pip
tools=(pip setuptools)
for pkg in ${tools[@]}; do
    echo "updating $pkg..."
    pip install -U $pkg >/dev/null
    if [ $? -ne 0 ]; then
        exit
    fi
done

# install packages listed in dependencies.txt
deps=$(cat dependencies.txt | grep -v "^#")
for pkg in ${deps[@]}; do
    echo "installing $pkg..."
    pip install $pkg >/dev/null
    if [ $? -ne 0 ]; then
        echo "failed to install $pkg"
        break
    fi
done
