#!/usr/bin/env python3
from OpenGL.GL import *  # noqa
from sdl2.ext import get_events
from surrender import Mesh
from surrender import MeshData
from surrender import Shader
from surrender import ShaderSource
from surrender import matlib
import argparse
import sdl2 as sdl
import surrender

WIDTH = 800
HEIGHT = 600

PROJECTION_MAT = None
MODELVIEW_MAT = None
TRANSFORM_MAT = None


def setup():
    global PROJECTION_MAT
    global MODELVIEW_MAT
    global TRANSFORM_MAT

    aspect = HEIGHT / float(WIDTH)
    PROJECTION_MAT = matlib.Mat()
    PROJECTION_MAT.persp(50, 1.0 / aspect, 1, 100)

    MODELVIEW_MAT = matlib.Mat()
    MODELVIEW_MAT.lookat(
        matlib.Vec(5, 5, 5),
        matlib.Vec(0, 0, 0),
        matlib.Vec(0, 1, 0))

    TRANSFORM_MAT = matlib.Mat()

    glClearColor(0.3, 0.3, 0.3, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)


def update(dt):
    global TRANSFORM_MAT
    TRANSFORM_MAT.identity()


def render(mesh, shader):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    shader.params['projection'].set(PROJECTION_MAT)
    shader.params['modelview'].set(MODELVIEW_MAT)
    shader.params['transform'].set(TRANSFORM_MAT)

    mesh.render()
    surrender.render()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Surrender python demo')
    parser.add_argument('mesh', type=str,
        help='Mesh file to render')

    args = parser.parse_args()

    # initialize renderer
    surrender.init(WIDTH, HEIGHT)

    # setup context and matrices
    setup()

    # load mesh
    md = MeshData.from_file(args.mesh)
    mesh = Mesh(md)

    # compile shaders
    sources = [
        ShaderSource.from_file('data/default.vert'),
        ShaderSource.from_file('data/default.frag'),
    ]

    # create and make active the shader program
    shader = Shader(*sources)
    shader.use()

    # main loop
    run = True
    while run:
        # process input
        events = get_events()
        for evt in events:
            if evt.type == sdl.SDL_KEYDOWN:
                run = False
                break

        # update logic
        update(0)

        # render
        render(mesh, shader)
