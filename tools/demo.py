#!/usr/bin/env python3
from abc import ABC
from OpenGL.GL import *
from enum import IntEnum
from enum import unique
from sdl2.ext import get_events
from surrender import AnimationInstance
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


class KeyEvent(Event):
    @unique
    class State(IntEnum):
        down = 0
        up = 1

    def __init__(self, key, state):
        self.key = key
        self.state = state


class App:

    def __init__(self, width, height, mesh_file):
        self.events = []
        self.play = False

        surrender.init(width, height)
        aspect = HEIGHT / float(WIDTH)
        self.projection_mat = matlib.Mat()
        self.projection_mat.persp(50, 1.0 / aspect, 1, 100)

        self.modelview_mat = matlib.Mat()
        self.modelview_mat.lookat(
            matlib.Vec(20, 20, 20),
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

        # instantiate animations
        self.animations = [
            AnimationInstance(anim) for anim in md.animations
        ]
        self.current_anim_idx = -1
        self.current_anim = self.next_anim()

        # compile shaders
        sources = [
            ShaderSource.from_file('data/default.vert'),
            ShaderSource.from_file('data/default.frag'),
        ]

        # create and make active the shader program
        self.shader = Shader(*sources)
        self.shader.use()

    def next_anim(self):
        if self.animations:
            if self.current_anim_idx < len(self.animations):
                self.current_anim_idx = (self.current_anim_idx + 1) % len(self.animations)
                self.reset_anim()
                return self.animations[self.current_anim_idx]
        return None

    def prev_anim(self):
        if self.animations:
            if self.current_anim_idx < len(self.animations):
                if self.current_anim_idx <= 0:
                    self.current_anim_idx = len(self.animations)
                self.current_anim_idx -= 1
                self.reset_anim()
                return self.animations[self.current_anim_idx]
        return None

    def reset_anim(self):
        print('current animation: {}'.format(self.current_anim_idx))

    def update(self, dt):
        self.transform_mat.identity()

        for evt in self.events:
            if type(evt) == KeyEvent:
                if evt.state == KeyEvent.State.up:
                    if evt.key in {sdl.SDLK_q, sdl.SDLK_ESCAPE}:
                        return False
                    elif evt.key == sdl.SDLK_LEFT:
                        self.current_anim = self.prev_anim()
                    elif evt.key == sdl.SDLK_RIGHT:
                        self.current_anim = self.next_anim()
                    elif evt.key == sdl.SDLK_SPACE:
                        self.play = not self.play
                        self.reset_anim()

        if self.play:
            self.current_anim.play(dt)

        return True

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shader.params['projection'].set(self.projection_mat)
        self.shader.params['modelview'].set(self.modelview_mat)
        self.shader.params['transform'].set(self.transform_mat)

        if self.play and self.current_anim:
            self.shader.params['animate'].set(1)
            self.shader.params['joints[0]'].set(self.current_anim.skin_transforms)
        else:
            self.shader.params['animate'].set(0)

        self.mesh.render()
        surrender.render()

    def process_input(self):
        events = get_events()
        for evt in events:
            if evt.type == sdl.SDL_KEYDOWN:
                self.events.append(KeyEvent(
                    evt.key.keysym.sym, KeyEvent.State.down))
            elif evt.type == sdl.SDL_KEYUP:
                self.events.append(KeyEvent(
                    evt.key.keysym.sym, KeyEvent.State.up))

    def start(self):
        last_update = sdl.SDL_GetTicks()

        while True:
            # compute delta time
            now = sdl.SDL_GetTicks()
            dt = (now - last_update) / 1000.
            last_update = now

            # process input
            self.process_input()

            # update logic
            if not self.update(dt):
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
