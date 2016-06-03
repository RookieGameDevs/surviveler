from PIL import Image
from configparser import ConfigParser
from itertools import chain
from main import CONFIG_FILE
from main import setup_logging
from matlib import Vec3
import click
import logging
import math


LOG = logging.getLogger(__name__)

EPSILON = 0.1
DEFAULT_PRECISION = 4


def in_triangle(point, triangle):
    A, B, C = map(lambda t: Vec3(*t), triangle)
    P = Vec3(*point)

    u = B - A
    v = C - A
    w = P - A

    vxw = v.cross(w)
    vxu = v.cross(u)

    if vxw.dot(vxu) < 0:
        return False

    uxw = u.cross(w)
    uxv = u.cross(v)

    if uxw.dot(uxv) < 0:
        return False

    denom = uxv.mag()
    r = vxw.mag() / denom
    t = uxw.mag() / denom

    return (r + t <= 1)


def exc(n):
    return int(math.copysign(math.ceil(abs(n)), n))


def mag(axis, faces):
    minimum = min(map(lambda v: v[axis], chain.from_iterable(faces)))
    maximum = max(map(lambda v: v[axis], chain.from_iterable(faces)))
    return exc(minimum), exc(maximum)


def s_width(faces):
    return mag(0, faces)


def s_height(faces):
    return mag(1, faces)


def is_walkable(p, d, face, step=0):
    walkable = not in_triangle([p[0] + d, p[1] + d], face)

    if not step:
        return walkable
    if walkable:
        px, py = p
        ps = [
            [px, py],
            [px + d, py],
            [px, py + d],
            [px + d, py + d]
        ]
        walkable = all(map(lambda x: is_walkable(x, d / 2, face, step - 1), ps))
    return walkable


def set_not_walkable(face, matrix, precision):
    x0, x1 = s_width([face])
    y0, y1 = s_height([face])
    for y in range(y0, y1):
        for x in range(x0, x1):
            if matrix[y][x]:
                d = 0.5
                matrix[y][x] = is_walkable([x, y], d, face, precision)


def calculate_matrix(faces, precision):
    relevant = list(
        filter(lambda face: all(map(lambda x: abs(x[2]) <= EPSILON, face)), faces))

    x0, x1 = s_width(relevant)
    y0, y1 = s_height(relevant)

    matrix = {
        y: {
            x: True
            for x in range(x0, x1)
        }
        for y in range(y0, y1)
    }

    for i, face in enumerate(relevant):
        LOG.info('Face {} of {}, ({}, {})'.format(i, len(relevant), s_width([face]), s_height([face])))
        set_not_walkable(face, matrix, precision)

    m = bytearray()
    for y in reversed(list(matrix.keys())):
        for x in sorted(matrix[y].keys()):
            m.append(255 if matrix[y][x] else 0)

    return (abs(x0 - x1), abs(y0 - y1)), m


def parse_faces(objfile):
    vertices = []
    faces = []

    def parse_vertex(data):
        vertices.append([float(component) for component in data])

    def parse_face(data):
        if len(data) != 3:
            raise Exception

        f = []
        for face in data:
            # convert index values to integers and normalize them to 0 base,
            # set missing indices to -1
            face_items = [int(i) - 1 if i else -1 for i in face.split('/')]

            # clamp items array to 3 elements
            if len(face_items) < 3:
                face_items.extend([-1] * (3 - len(face_items)))

            f.append(vertices[face_items[0]])

        faces.append(f)

    for l in objfile:
        tokens = l.split()
        t, data = tokens[0], tokens[1:]
        if t == 'v':
            parse_vertex(data)
        elif t == 'f':
            parse_face(data)

    return faces


@click.command()
@click.argument(
    'objfile',
    type=click.File())
@click.argument(
    'target',
    type=click.File(mode='wb')
)
@click.option('--precision', default=DEFAULT_PRECISION)
def main(objfile, target, precision):
    faces = parse_faces(objfile)
    size, m = calculate_matrix(faces, precision)
    i = Image.frombytes('L', size, bytes(m))
    i.save(target, format='bmp')


if __name__ == '__main__':
    config = ConfigParser()
    config.read(CONFIG_FILE)
    setup_logging(config['Logging'])
    main()
