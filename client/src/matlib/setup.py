from distutils.core import Extension
from distutils.core import setup

module = Extension(
    'matlib',
    extra_compile_args=[
        '-std=c99',
        '-Wall',
    ],
    libraries=['cblas'],
    sources=['matlib.c'])

setup(
    name='matlib',
    version='0.1',
    description='Fast math library',
    ext_modules=[module])
