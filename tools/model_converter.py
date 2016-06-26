#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Model import tool which converts model data into native binary format."""

from struct import pack
import argparse
import pyassimp


class VertexFormat(object):

    has_coord = 1
    has_normal = 1 << 1
    has_uv = 1 << 2
    has_weight = 1 << 3


class DataFormatError(Exception):
    pass


def main(model, out):
    scene = pyassimp.load(model)

    if scene.mNumMeshes != 1:
        raise DataFormatError('File expected to contain exactly one mesh')

    mesh = scene.meshes[0]

    # determine output format
    fmt = 0
    v_count = len(mesh.vertices)
    n_count = len(mesh.normals)
    t_count = len(mesh.texturecoords)
    b_count = len(mesh.bones)

    if n_count > 0:
        fmt |= VertexFormat.has_normal
    # if t_count > 0:
    #     fmt |= VertexFormat.has_uvs
    # if b_count > 0:
    #     fmt |= VertexFormat.has_bones

    with open(out, 'wb') as fp:
        # write header
        header = pack('<hLLB', fmt, v_count, v_count, b_count)
        fp.write(header)

        # write vertices
        for x, y, z in mesh.vertices:
            v = pack('<fff', x, y, z)
            fp.write(v)

        # write normals
        for x, y, z in mesh.normals:
            v = pack('<fff', x, y, z)

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
