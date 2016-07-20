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


class App:

    def __init__(self, width, height, mesh_file):
        surrender.init(width, height)
        aspect = HEIGHT / float(WIDTH)
        self.projection_mat = matlib.Mat()
        self.projection_mat.persp(50, 1.0 / aspect, 1, 100)

        self.modelview_mat = matlib.Mat()
        self.modelview_mat.lookat(
            matlib.Vec(5, 5, 5),
            matlib.Vec(0, 0, 0),
            matlib.Vec(0, 1, 0))

        self.transform_mat = matlib.Mat()

        glClearColor(0.3, 0.3, 0.3, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        self.load(mesh_file)

    def __del__(self):
        surrender.shutdown()

    def load(self, mesh_file):
        # load mesh
        md = MeshData.from_file(mesh_file)
        self.mesh = Mesh(md)

        # compile shaders
        sources = [
            ShaderSource.from_file('data/default.vert'),
            ShaderSource.from_file('data/default.frag'),
        ]

        # create and make active the shader program
        self.shader = Shader(*sources)
        self.shader.use()

    def update(self, dt):
        self.transform_mat.identity()

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shader.params['projection'].set(self.projection_mat)
        self.shader.params['modelview'].set(self.modelview_mat)
        self.shader.params['transform'].set(self.transform_mat)

        self.mesh.render()

        surrender.render()

    def start(self):
        run = True
        while run:
            # process input
            events = get_events()
            for evt in events:
                if evt.type == sdl.SDL_KEYDOWN:
                    run = False
                    break

            # update logic
            self.update(0)

            # render
            self.render()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Surrender python demo')
    parser.add_argument('mesh', type=str,
        help='Mesh file to render')

    args = parser.parse_args()

    demo = App(WIDTH, HEIGHT, args.mesh)
    demo.start()
