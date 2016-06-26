#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Model import tool which converts model data into native binary format."""

from struct import pack
import argparse
import pyassimp

VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION = VERSION_MINOR << 4 | VERSION_MAJOR


class VertexFormat(object):

    has_position = 1
    has_normal = 1 << 1
    has_uv = 1 << 2
    has_joints = 1 << 3


class DataFormatError(Exception):
    pass


def main(model, out):
    scene = pyassimp.load(model)

    if scene.mNumMeshes != 1:
        raise DataFormatError('File expected to contain exactly one mesh')

    mesh = scene.meshes[0]

    # determine output format
    fmt = VertexFormat.has_position

    v_count = len(mesh.vertices)
    n_count = len(mesh.normals)
    t_count = len(mesh.texturecoords)
    b_count = len(mesh.bones)

    if n_count > 0:
        fmt |= VertexFormat.has_normal
    if t_count > 0:
        fmt |= VertexFormat.has_uvs
    if b_count > 0:
        fmt |= VertexFormat.has_joints

    with open(out, 'wb') as fp:
        # write header
        header = pack('<bhLLB', VERSION, fmt, v_count, v_count, b_count)
        fp.write(header)

        # write vertices
        for v in range(v_count):
            px, py, pz = mesh.vertices[v]
            fp.write(pack('<fff', px, py, pz))

            if fmt & VertexFormat.has_normal:
                nx, ny, nz = mesh.normals[v]
                fp.write(pack('<fff', nx, ny, nz))

        # write indices
        for i in range(len(mesh.vertices)):
            fp.write(pack('<L', i))

    pyassimp.release(scene)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converter to native binary format.')
    parser.add_argument('model', type=str, help='Model source file')
    parser.add_argument('out', type=str, help='Destination file')

    args = parser.parse_args()

    try:
        main(args.model, args.out)
    except DataFormatError as err:
        print 'Conversion failed: {}'.format(err)
