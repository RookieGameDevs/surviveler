from distutils.core import Extension
from distutils.core import setup


cflags = [
    '-std=c99',
    '-Wall',
    '-O3',
    '-DWITH_PYTHON',
]

libs = [
    'cblas',
]

module = Extension(
    'matlib',
    extra_compile_args=cflags,
    libraries=libs,
    sources=['matlib.c'])

setup(
    name='matlib',
    version='0.1',
    description='Fast math library',
    ext_modules=[module])
