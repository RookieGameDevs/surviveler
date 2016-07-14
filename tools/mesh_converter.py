#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Model import tool which converts model data into native binary format."""

from collections import defaultdict
from itertools import chain
from itertools import count
from struct import pack
import argparse
import os
import pyassimp


VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION = VERSION_MINOR << 4 | VERSION_MAJOR

MAX_JOINTS_PER_VERTEX = 4

IDENTITY_MATRIX = [
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
]


class VertexFormat(object):

    has_position = 1
    has_normal = 1 << 1
    has_uv = 1 << 2
    has_joints = 1 << 3


class DataFormatError(Exception):
    pass


def traverse_children(node, op):
    for child in node.children:
        if op(child):
            traverse_children(child, op)


def traverse_scene(scene, op):
    op(scene.rootnode)
    traverse_children(scene.rootnode, op)


def traverse_parents(scene, node, op):
    op(node)
    if node.parent != scene:
        traverse_parents(scene, node.parent, op)


def find_root(nodes):
    root = None
    for node in nodes:
        if node.parent not in nodes:
            if root is not None:
                raise DataFormatError('inconsistent skeleton hierarchy')
            root = node
    return root


def load_animations(scene, skeleton, counter):
    animations = {}
    for i, anim in enumerate(scene.animations):
        name = 'anim{}'.format(next(counter))

        if len(anim.channels) == 0 or len(anim.channels[0].positionkeys) == 0:
            raise DataFormatError('animation "{}" has no keyframes'.format(name))

        timestamps = list(sorted([
            pos.time for pos in anim.channels[0].positionkeys
        ]))

        # build local node timelines
        node_timelines = {}
        for node in anim.channels:
            node_name = node.nodename.data
            node_timeline = {}
            for pos, rot, scale in zip(node.positionkeys, node.rotationkeys, node.scalingkeys):
                t = pos.time
                if pos.time != rot.time or rot.time != scale.time:
                    raise DataFormatError(
                        'node "{}" in animation "{}" has inconsistent channel timeline'.format(
                            node_name,
                            name))
                node_timeline[t] = (pos.value, rot.value, scale.value)
            node_timelines[node_name] = node_timeline

            # assert local node timelines match the global one
            node_timestamps = list(sorted(node_timeline.keys()))
            if node_timestamps != timestamps:
                raise DataFormatError(
                    'node "{}" in animation "{}" local timeline does not match '
                    'global timeline'.format(
                        node_name,
                        name))

        # inject identity transformations for non-joint animation nodes for each
        # timestamp in the timeline
        node_timelines.update({
            node_name: {
                t: (
                    # position
                    [0, 0, 0],
                    # rotation
                    [1, 0, 0, 0],
                    # scale
                    [1, 1, 1],
                ) for t in timestamps
            } for node_name in set(skeleton) - set(node_timelines)
        })

        # fill the pose data
        pose_data = []
        for t in timestamps:
            skeleton_pose = []
            for node_name, timeline in node_timelines.iteritems():
                try:
                    joint_id = skeleton[node_name][0]
                except KeyError:
                    raise DataFormatError(
                        'animation "{}" skeleton does not match reference one'.format(name))
                pos, rot, scale = timeline[t]
                skeleton_pose.append((joint_id, pos, rot, scale))

            # sort joint poses by joint_id
            skeleton_pose = sorted(skeleton_pose, key=lambda p: p[0])
            pose_data.extend(skeleton_pose)

        animations[name] = (timestamps, pose_data, anim.duration, anim.tickspersecond)

    return animations


def load_skeleton(scene):
    skeleton = {}
    mesh = scene.meshes[0]

    def mark_node(n, flag):
        skeleton_parts.setdefault(n.name, [False, n])
        skeleton_parts[n.name][0] = flag
        return True

    # create a mapping with nodes which are part of the skeleton
    skeleton_parts = {}
    bones_by_name = {}
    traverse_scene(scene, lambda n: mark_node(n, False))
    for bone in mesh.bones:
        bones_by_name[bone.name] = bone
        # mark node and its parents as part of the skeleton
        node = skeleton_parts[bone.name][1]
        traverse_parents(
            scene,
            node,
            lambda n: mark_node(n, True))

    # find the root node for nodes which are part of the skeleton
    skeleton_root = find_root([
        node_info[1] for node_info in
        skeleton_parts.itervalues()
        if node_info[0]
    ])

    # build up the skeleton starting from root and including only node
    # branches which are required
    joint_id = count()

    def add_to_skeleton(node):
        is_part = skeleton_parts[node.name][0]
        if is_part:
            if node == scene.rootnode:
                parent_id = 255
            else:
                parent_id = skeleton[node.parent.name][0]
            transform = (
                bones_by_name[node.name].offsetmatrix
                if node.name in bones_by_name
                else IDENTITY_MATRIX)
            skeleton[node.name] = (
                next(joint_id),  # joint id
                parent_id,  # parent id
                transform)  # joint transform
        return is_part

    add_to_skeleton(skeleton_root)
    traverse_children(skeleton_root, add_to_skeleton)

    # populate per-vertex joint attribute data
    vertex_bone_weights = defaultdict(list)
    vertex_bone_ids = defaultdict(list)
    for bone in mesh.bones:
        for vw in bone.weights:
            v_id = vw.vertexid
            j_id = skeleton[bone.name][0]
            vertex_bone_ids[v_id].append(j_id)
            vertex_bone_weights[v_id].append(int(round(vw.weight * 255)))

            bindings_count = len(vertex_bone_ids[v_id])
            if bindings_count > MAX_JOINTS_PER_VERTEX:
                msg = 'vertex {} exceeds max joint bindings count {}/{}'.format(
                    v_id, bindings_count, MAX_JOINTS_PER_VERTEX)
                print(msg)
                vertex_bone_ids[v_id] = vertex_bone_ids[v_id][:MAX_JOINTS_PER_VERTEX]
                vertex_bone_weights[v_id] = vertex_bone_weights[v_id][:MAX_JOINTS_PER_VERTEX]
                continue

    return skeleton, vertex_bone_ids, vertex_bone_weights


def main(mesh, out, anims=None):
    scene = pyassimp.load(mesh)

    anim_counter = count(0)
    animations = {}
    skeleton = {}

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
        fmt |= VertexFormat.has_uv
    if b_count > 0:
        fmt |= VertexFormat.has_joints

    if fmt & VertexFormat.has_joints:
        skeleton, vertex_bone_ids, vertex_bone_weights = load_skeleton(scene)
        for anim_file in anims or []:
            anim_scene = pyassimp.load(anim_file)
            animations.update(load_animations(anim_scene, skeleton, anim_counter))
        strings = {s: i for i, s in enumerate(animations.iterkeys())}

    with open(out, 'wb') as fp:
        # write header
        header = pack(
            '<bhLLBH',
            VERSION,
            fmt,
            v_count,
            v_count,
            len(skeleton),
            len(animations))
        fp.write(header)

        # write root transformation
        for val in chain.from_iterable(scene.rootnode.transformation):
            fp.write(pack('<f', val))

        # write vertices
        for v in range(v_count):
            # position
            px, py, pz = mesh.vertices[v]
            fp.write(pack('<fff', px, py, pz))

            # normal
            if fmt & VertexFormat.has_normal:
                nx, ny, nz = mesh.normals[v]
                fp.write(pack('<fff', nx, ny, nz))

            # UV
            if fmt & VertexFormat.has_uv:
                tx, ty, _ = mesh.texturecoords[0][v]
                fp.write(pack('<ff', tx, ty))

            # joint data
            if fmt & VertexFormat.has_joints:
                ids, weights = vertex_bone_ids.get(v, []), vertex_bone_weights.get(v, [])

                # extend the arrays to size equal to MAX_JOINTS_PER_VERTEX
                bindings_count = len(ids)
                ids.extend([255] * (MAX_JOINTS_PER_VERTEX - bindings_count))
                weights.extend([0] * (MAX_JOINTS_PER_VERTEX - bindings_count))

                for attr in ids + weights:
                    fp.write(pack('<B', attr))

        # write indices
        for i in range(len(mesh.vertices)):
            fp.write(pack('<L', i))

        # write joints
        for j_id, p_id, transform in sorted(skeleton.values(), key=lambda j: j[0]):
            fp.write(pack('<BB', j_id, p_id))
            for row in transform:
                fp.write(pack('<ffff', *row))

        # write animations
        for name, (timestamps, poses, duration, tickspersecond) in animations.iteritems():
            # header
            fp.write(pack(
                '<LffL',
                strings[name],
                duration,
                tickspersecond,
                len(timestamps)))

            # timestamps
            for t in timestamps:
                fp.write(pack('<f', t))

            # pose data
            for joint_id, pos, rot, scale in poses:
                pose = pack(
                    '<Bffffffffff',
                    joint_id,
                    pos[0], pos[1], pos[2],
                    rot[0], rot[1], rot[2], rot[3],
                    scale[0], scale[1], scale[2])
                fp.write(pose)

        # write strings
        for string in strings:
            try:
                enc_string = string.encode('ascii')
            except UnicodeEncodeError:
                raise DataFormatError(
                    u'{} non-ascii string constants are not allowed'.format(string))
            fp.write(pack('<{}sb'.format(len(enc_string)), enc_string, 0))

    print('Mesh file:  {}'.format(out))
    print('Mesh size:  {} bytes'.format(os.stat(out).st_size))
    print('Polygons:   {}'.format(len(mesh.faces)))
    print('Vertices:   {}'.format(v_count))
    print('Indices:    {}'.format(v_count))
    print('Joints:     {}'.format(len(skeleton)))
    for name, (timeline, pose_data, duration, tickspersecond) in animations.items():
        print('Animation   "{}"'.format(name))
        print('  Duration: {}'.format(duration))
        print('  Speed:    {}'.format(tickspersecond))
        print('  Keys:     {}'.format(len(timeline)))

    pyassimp.release(scene)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converter to native binary format.')
    parser.add_argument('--mesh', type=str, required=True, help='Mesh file')
    parser.add_argument('--anims', type=str, nargs='+', help='Animation file')
    parser.add_argument('-o', type=str, help='Output filename')

    args = parser.parse_args()

    try:
        main(args.mesh, args.o, anims=args.anims or None)
    except DataFormatError as err:
        print 'Conversion failed: {}'.format(err)
