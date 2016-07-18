#!/usr/bin/env python3
from surrender import MeshData
from surrender import Shader
from surrender import ShaderSource
import argparse
import surrender


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Surrender python demo')
    parser.add_argument('mesh', type=str,
        help='Mesh file to render')

    args = parser.parse_args()

    surrender.init(800, 600)

    md = MeshData.from_file(args.mesh)
    sources = [
        ShaderSource.from_file('data/default.vert'),
        ShaderSource.from_file('data/default.frag'),
    ]
    shader = Shader(*sources)
