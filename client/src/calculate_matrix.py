from PIL import Image
from configparser import ConfigParser
from functools import partial
from itertools import chain
from main import CONFIG_FILE
from main import setup_logging
from matlib import Vec
import click
import logging
import math
import multiprocessing as mp
import numpy as np


LOG = logging.getLogger(__name__)

EPSILON = 0.1
DEFAULT_PRECISION = 4
GRID_CELL = 0.5


def is_degenerate(triangle):
    """Checks if the triangle is degenerate.

    :param triangle: The triangle to be checked.
    :type triangle: list

    :return: Wether the triangle is degenerate or not
    :rtype: bool
    """
    A, B, C = map(lambda t: Vec(*t), triangle)
    u = B - A
    v = C - A
    uxv = u.cross(v)
    return uxv.mag() == 0


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
    A, B, C = map(lambda t: Vec(*t), triangle)
    P = Vec(*point)

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


def excess(n):
    """Round by excess taking the sign into consideration.

    :param n: The number to be rounded
    :type n: float

    :return: The signed rounded items
    :rtype: int
    """
    return int(math.copysign(math.ceil(abs(n)), n))


def defect(n):
    """Round by defect taking the sign into consideration.

    :param n: The number to be rounded
    :type n: float

    :return: The signed rounded items
    :rtype: int
    """
    return int(math.copysign(math.floor(abs(n)), n))


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
    return min(defect(minimum), excess(minimum)), max(defect(maximum), excess(maximum))


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


def set_not_walkable(face, matrix, precision, grid_cell):
    """Sets all the non_walkable cells on the matrix. Considers only a single
    triangle.

    :param face: The triangle
    :type face: list

    :param matrix: The level walkable matrix, modified in place
    :type matrix: dict

    :param precision: The number of recursive calls to be done
    :type precision: int

    :param grid_cell: The size of the grid cell edge
    :type grid_cell: float
    """
    x0, x1 = s_width([face])
    y0, y1 = s_height([face])
    # Iterate over the bounding box of the face to check every possible cell
    # that can be not walkable.
    for y in np.arange(y0, y1, grid_cell):
        if y not in matrix:
            continue
        for x in np.arange(x0, x1, grid_cell):
            # Avoid completely the check in case the cell is already considered
            # non-walkable.
            if x not in matrix[y]:
                continue
            if matrix[y][x]:
                # NOTE: only updates the matrix in case the cell is considered
                # not walkable.
                if not is_walkable([x, y], grid_cell / 2, face, precision):
                    matrix[y][x] = False


def process_face(x_axis, y_axis, precision, grid_cell, values):
    """Process worker"""
    x0, x1 = x_axis
    y0, y1 = y_axis
    matrix = {
        y: {
            x: True
            for x in np.arange(x0, x1, GRID_CELL)
        }
        for y in np.arange(y0, y1, GRID_CELL)
    }

    i, face = values
    LOG.info('Face {}, ({}, {})'.format(i + 1, s_width([face]), s_height([face])))
    set_not_walkable(face, matrix, precision, grid_cell)
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


def calculate_matrix(faces, precision, grid_cell):
    """Matrix calculation main routine.

    :param faces: The list of all the faces parsed from the level obj file.
    :type faces: list

    :param precision: The precision of the matrix computation
    :type precision: int

    :param grid_cell: The size of the grid cell edge
    :type grid_cell: float

    :return: The generated level walkable matrix
    :rtype: dict
    """
    # Filter out non-relevant faces.
    # NOTE: relevant faces are the ones completely on the xy plane where
    # (z <= EPSILON).
    def f_func(face):
        """Filter function for relevant faces.
        """
        on_floor = all(map(lambda x: abs(x[2]) <= EPSILON, face))
        return on_floor and not is_degenerate(face)

    relevant = list(
        filter(f_func, faces))

    # Get the bounding box of the map
    x0, x1 = s_width(relevant)
    y0, y1 = s_height(relevant)

    LOG.info('Map bounding box: {}, {}'.format((x0, x1), (y0, y1)))

    with mp.Pool() as pool:
        LOG.info('Found {} faces to be analyzed'.format(len(relevant)))
        results = pool.map(partial(process_face, (x0, x1), (y0, y1), precision, grid_cell), enumerate(relevant))

        pool.close()
        pool.join()

        LOG.info('Calculation finished: generating the matrix')
        matrix = {
            y: {
                x: True
                for x in np.arange(x0, x1, grid_cell)
            }
            for y in np.arange(y0, y1, grid_cell)
        }
        for r in results:
            merge(matrix, r)

        # Create a bytearray matrix
        m = bytearray()
        for y in sorted(matrix.keys(), reverse=True):
            for x in sorted(matrix[y].keys()):
                m.append(255 if matrix[y][x] else 0)

    return (int(abs(x0 - x1) / grid_cell), int(abs(y0 - y1) / grid_cell)), m


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
@click.option('--grid-cell', default=GRID_CELL)
def main(objfile, target, precision, grid_cell):
    faces = parse_faces(objfile)
    size, m = calculate_matrix(faces, precision, grid_cell)
    i = Image.frombytes('L', size, bytes(m))
    i.save(target, format='bmp')


if __name__ == '__main__':
    config = ConfigParser()
    config.read(CONFIG_FILE)
    setup_logging(config['Logging'])
    main()
