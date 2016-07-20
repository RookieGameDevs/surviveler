#!/usr/bin/env python3
from abc import ABC
from OpenGL.GL import *  # noqa
from enum import IntEnum
from enum import unique
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


class Event(ABC):
    """Base class for events"""


class KeyboardEvent(Event):
    @unique
    class KeyState(IntEnum):
        pressed = 0
        released = 1

    def __init__(self, key, state):
        self.key = key
        self.state = state


class App:

    def __init__(self, width, height, mesh_file):
        self.events = []

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

        for evt in self.events:
            if type(evt) == KeyboardEvent:
                if evt.key in {sdl.SDLK_q, sdl.SDLK_ESCAPE}:
                    return False

        return True

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shader.params['projection'].set(self.projection_mat)
        self.shader.params['modelview'].set(self.modelview_mat)
        self.shader.params['transform'].set(self.transform_mat)

        self.mesh.render()
        surrender.render()

    def process_input(self):
        events = get_events()
        for evt in events:
            if evt.type == sdl.SDL_KEYDOWN:
                self.events.append(KeyboardEvent(
                    evt.key.keysym.sym,
                    KeyboardEvent.KeyState.pressed))
            elif evt.type == sdl.SDL_KEYUP:
                self.events.append(KeyboardEvent(
                    evt.key.keysym.sym,
                    KeyboardEvent.KeyState.released))

    def start(self):
        while True:
            # process input
            self.process_input()

            # update logic
            if not self.update(0):
                break

            # render
            self.render()

            self.events = []


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Surrender python demo')
    parser.add_argument('mesh', type=str,
        help='Mesh file to render')

    args = parser.parse_args()

    demo = App(WIDTH, HEIGHT, args.mesh)
    demo.start()
