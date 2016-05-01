#!/bin/bash

source bin/activate
PYTHONPATH=$PWD/src py.test src
