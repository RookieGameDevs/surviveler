# -*- coding: utf-8 -*-
import sys

def options(opt):
    opt.load('compiler_c')
    opt.load('compiler_cxx')

    opt.add_option(
        '--build-type',
        action='store',
        choices=['release', 'debug'],
        default='debug',
        help='build type (release or debug)')

    opt.add_option(
        '--with-python',
        action='store_true',
        help='build python extension')


def configure(cfg):
    cfg.load('compiler_c')
    cfg.load('compiler_cxx')

    cfg.env.append_unique('CFLAGS', '-std=c99')
    cfg.env.append_unique('CFLAGS', '-Wall')
    cfg.env.append_unique('INCLUDES', cfg.path.find_dir('src').abspath())
    if cfg.options.build_type == 'debug':
        cfg.env.append_unique('CFLAGS', '-g')
        cfg.env.append_unique('CXXFLAGS', '-g')
        cfg.env.append_unique('DEFINES', 'DEBUG')
    else:
        cfg.env.append_unique('CFLAGS', '-O3')

    cfg.env.with_python = cfg.options.with_python

    # find Python
    if cfg.options.with_python:
        cfg.check_cfg(
            path='python3-config',
            args='--cflags',
            package='',
            uselib_store='python')

    # find SDL2
    cfg.check_cfg(
        path='sdl2-config',
        args='--libs --cflags',
        package='',
        uselib_store='sdl')

    # find GLEW
    cfg.check_cfg(
        package='glew',
        args='--libs --cflags',
        uselib_store='glew')

    if sys.platform.startswith('linux'):
        # find libm (standard C math library)
        cfg.check_cc(
            msg=u'Checking for libm',
            lib='m',
            cflags='-Wall',
            uselib_store='libm')

        # find CBLAS library (of any implementation)
        cfg.check_cc(
            msg=u'Checking for BLAS library',
            lib='blas',
            header_name='cblas.h',
            uselib_store='cblas')


def build(bld):
    # build library
    libs = [
        'sdl',
        'glew',
    ]
    kwargs = {
        'features': 'c cshlib',
        'target': 'surrender',
        'source': bld.path.ant_glob('src/**/*.c', excl=['**/python', 'src/main.c']),
        'uselib': libs,
    }

    if sys.platform.startswith('linux'):
        libs.extend([
            'libm',
            'cblas',
        ])
    elif sys.platform.startswith('darwin'):
        kwargs['framework'] = ['OpenGL', 'Accelerate']
    bld(**kwargs)

    # build demo executable
    bld.program(
        target='demo',
        source=[bld.path.find_node('src/main.c')],
        uselib=libs,
        rpath=[bld.bldnode.abspath()],
        use=['surrender'])

    # build python extension
    if bld.env.with_python:
        bld.shlib(
            target='python/surrender',
            source=bld.path.ant_glob('src/python/*.c'),
            includes=['src/python'],
            uselib=['python'])
