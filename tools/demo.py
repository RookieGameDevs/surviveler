#!/usr/bin/env python3
from OpenGL.GL import *  # noqa
from surrender import Mesh
from surrender import MeshData
from surrender import Shader
from surrender import ShaderSource
import argparse
import surrender


def setup():
    glClearColor(0.3, 0.3, 0.3, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)


def render(mesh):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    mesh.render()
    surrender.render()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Surrender python demo')
    parser.add_argument('mesh', type=str,
        help='Mesh file to render')

    args = parser.parse_args()

    surrender.init(800, 600)
    setup()

    # load mesh
    md = MeshData.from_file(args.mesh)
    mesh = Mesh(md)

    # load shaders
    sources = [
        ShaderSource.from_file('data/default.vert'),
        ShaderSource.from_file('data/default.frag'),
    ]
    shader = Shader(*sources)

    while True:
        render(mesh)
