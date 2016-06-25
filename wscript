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

    # find SDL_ttf (version2)
    # cfg.check_cfg(
    #     package='SDL2_ttf',
    #     args='--libs --cflags',
    #     uselib_store='sdl2_ttf')

    # find GLib
    # cfg.check_cfg(
    #     package='glib-2.0',
    #     args='--libs --cflags',
    #     uselib_store='glib')

    # find assimp
    # cfg.check_cfg(
    #     package='assimp',
    #     args='--libs --cflags',
    #     uselib_store='assimp')

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
    libs = [
        'sdl',
        'glew',
        # 'sdl2_ttf',
        # 'glib',
        # 'assimp',
        # 'bullet',
    ]
    kwargs = {
        'features': 'c cprogram',
        'target': 'demo',
        'source': bld.path.ant_glob('src/**/*.c'),
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
