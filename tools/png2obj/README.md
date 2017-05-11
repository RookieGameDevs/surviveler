# png2obj

This tool create a mesh from a png image, assuming each non-white-or-transparent pixel being a non-walkable wall.

## Usage

$ python3 png2obj.py path/to/level.png

## Test

From this directory, do:

$ PYTHONPATH=$PWD py.test

An obj file is created for each png sample.
So, to remove all test artifacts just remove the created .obj files.
