from PIL import Image
from configparser import ConfigParser
from functools import partial
from itertools import chain
from main import CONFIG_FILE
from main import setup_logging
from matlib import Vec3
import click
import logging
import math
import multiprocessing as mp


LOG = logging.getLogger(__name__)

EPSILON = 0.1
DEFAULT_PRECISION = 4


def in_triangle(point, triangle):
    """Checks if a specified point is inside a triangle using the barycenter
    technique.

    :param point: The point to be checked
    :type point: list

    :param triangle: The triangle
    :type triangle: list

    :return: True if the point is inside the triangle.
    :rtype: bool
    """
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
    """Round by excess taking the sign into consideration.

    :param n: The number to be rounded
    :type n: float

    :return: The signed rounded items
    :rtype: int
    """
    return int(math.copysign(math.ceil(abs(n)), n))


def mag(axis, faces):
    """Calculate the minimum and maximum of the given list of faces on the
    specified axis. Rounded up (or down for negatives).

    :param axis: The index of the axis in the points of the faces
    :type axis: int

    :param faces: The list of faces to be considered
    :type faces: int, int

    :return: The minimum and maximum
    :rtype: tuple
    """
    minimum = min(map(lambda v: v[axis], chain.from_iterable(faces)))
    maximum = max(map(lambda v: v[axis], chain.from_iterable(faces)))
    return exc(minimum), exc(maximum)


def s_width(faces):
    """Calculate the minimum and maximum of the given list of faces on the
    x-axis. Rounded up (or down for negatives).

    :param faces: The list of faces to be considered
    :type faces: int, int

    :return: The minimum and maximum
    :rtype: tuple
    """
    return mag(0, faces)


def s_height(faces):
    """Calculate the minimum and maximum of the given list of faces on the
    y-axis. Rounded up (or down for negatives).

    :param faces: The list of faces to be considered
    :type faces: int, int

    :return: The minimum and maximum
    :rtype: tuple
    """
    return mag(1, faces)


def is_walkable(p, d, face, step=0):
    """Recursive function that calculates the walkability of a single cell.

    :param p: The point
    :type p: list

    :param d: The offset of the barycenter of the cell to be analized.
    :type d: float

    :param face: The triangle that we are considering
    :type face: list

    :param step: Recursion helper variable
    :type step: int

    :return: Boolean representing the walkability of the cell
    :rtype: bool
    """
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
    """Sets all the non_walkable cells on the matrix. Considers only a single
    triangle.

    :param face: The triangle
    :type face: list

    :param matrix: The level walkable matrix, modified in place
    :type matrix: dict

    :param precision: The number of recursive calls to be done
    :type precision: int
    """
    x0, x1 = s_width([face])
    y0, y1 = s_height([face])
    # Iterate over the bounding box of the face to check every possible cell
    # that can be not walkable.
    for y in range(y0, y1):
        for x in range(x0, x1):
            # Avoid completely the check in case the cell is already considered
            # non-walkable.
            if matrix[y][x]:
                d = 0.5
                # NOTE: only updates the matrix in case the cell is considered
                # not walkable.
                if not is_walkable([x, y], d, face, precision):
                    matrix[y][x] = False


def process_face(x_axis, y_axis, precision, values):
    """Process worker"""
    x0, x1 = x_axis
    y0, y1 = y_axis
    matrix = {
        y: {
            x: True
            for x in range(x0, x1)
        }
        for y in range(y0, y1)
    }

    i, face = values
    LOG.info('Face {}, ({}, {})'.format(i + 1, s_width([face]), s_height([face])))
    set_not_walkable(face, matrix, precision)
    return matrix


def merge(matrix, part):
    """Merge the matrix with the single partial.

    :param matrix: The result matrix
    :type matrix: dict

    :param part: The partial result to be merged
    :type part: dict
    """
    for y, v in part.items():
        if y not in matrix:
            matrix[y] = v
        for x, value in v.items():
            if x not in matrix[y]:
                matrix[y][x] = value
            else:
                matrix[y][x] &= value


def calculate_matrix(faces, precision):
    """Matrix calculation main routine.

    :param faces: The list of all the faces parsed from the level obj file.
    :type faces: list

    :param precision: The precision of the matrix computation
    :type precision: int

    :return: The generated level walkable matrix
    :rtype: dict
    """
    # Filter out non-relevant faces.
    # NOTE: relevant faces are the ones completely on the xy plane where
    # (z <= EPSILON).
    relevant = list(
        filter(lambda face: all(map(lambda x: abs(x[2]) <= EPSILON, face)), faces))

    # Get the bounding box of the map
    x0, x1 = s_width(relevant)
    y0, y1 = s_height(relevant)

    with mp.Pool() as pool:
        LOG.info('Found {} faces to be analyzed'.format(len(relevant)))
        results = pool.map(partial(process_face, (x0, x1), (y0, y1), precision), enumerate(relevant))

        pool.close()
        pool.join()

        LOG.info('Calculation finished: generating the matrix')
        matrix = {}
        for r in results:
            merge(matrix, r)

        # Create a bytearray matrix
        m = bytearray()
        for y in reversed(list(matrix.keys())):
            for x in sorted(matrix[y].keys()):
                m.append(255 if matrix[y][x] else 0)

    return (abs(x0 - x1), abs(y0 - y1)), m


def parse_faces(objfile):
    """Easy function for parsing the level faces from the level obj file.

    :param objfile: The objfile to be parsed
    :type objfile: :class:`File`

    :return: The list of parsed faces
    :rtype: list
    """
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
