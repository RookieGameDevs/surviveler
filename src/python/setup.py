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

sources = [
    'anim.c',
    'surrender.c',
]

module = Extension(
    'surrender',
    extra_compile_args=cflags,
    libraries=libs,
    sources=sources)

setup(
    name='surrender',
    version='0.1',
    description='Surviveler renderer',
    ext_modules=[module])
