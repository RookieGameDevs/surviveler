#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Model import tool which converts model data into native binary format."""

from struct import pack
import argparse
import pyassimp


class VertexFormat(object):

    has_normals = 1
    has_uvs = 1 << 1
    has_bones = 1 << 2


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
        fmt |= VertexFormat.has_normals
    if t_count > 0:
        fmt |= VertexFormat.has_uvs
    if b_count > 0:
        fmt |= VertexFormat.has_bones

    with open(out, 'wb') as fp:
        # write header
        header = pack('hLLB', fmt, v_count, v_count, b_count)
        fp.write(header)

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
