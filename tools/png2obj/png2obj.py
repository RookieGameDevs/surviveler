from PIL import Image
import logging
import numpy as np
import os
import sys
from collections import OrderedDict
from collections import deque
from collections import namedtuple
from typing import Dict
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Tuple

Pos = Tuple[int, int]
Vertex2D = Tuple[float, float]
Vector2D = Vertex2D
WallPerimeter = List[Vertex2D]
WalkableMatrix = List[List[int]]


EXAMPLE = np.array(
    [
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
    ],
    np.uint8
)


Box = namedtuple('Box', ['x', 'y'])
NearVertices = namedtuple('NearVertices', ['left', 'up', 'right', 'down'])
NearBoxes = namedtuple('NearBoxes', ['upleft', 'upright', 'downright', 'downleft'])


ROW = np.array(
    [
        [255, 0, 0, 0, 255],
        [255, 255, 255, 255],
    ])


LEFT = (-1, 0)
UP = (0, -1)
RIGHT = (1, 0)
DOWN = (0, 1)
HERE = (0, 0)
VERSOR_NAME = {
    LEFT: 'left', UP: 'up', RIGHT: 'right', DOWN: 'down', HERE: 'here'
}  # type: Dict[Vector2D, str]


POSSIBLE_DIRECTIONS = {
    ((0, 0),
     (0, 0)): (HERE, HERE),
    ((0, 0),
     (0, 1)): (RIGHT, DOWN),
    ((0, 0),
     (1, 0)): (LEFT, DOWN),
    ((0, 0),
     (1, 1)): (LEFT, RIGHT),
    ((0, 1),
     (0, 0)): (UP, RIGHT),
    ((0, 1),
     (0, 1)): (UP, DOWN),
    ((0, 1),
     (1, 0)): (LEFT, UP, RIGHT, DOWN),
    ((0, 1),
     (1, 1)): (LEFT, UP),
    ((1, 0),
     (0, 0)): (LEFT, UP),
    ((1, 0),
     (0, 1)): (LEFT, UP, RIGHT, DOWN),
    ((1, 0),
     (1, 0)): (UP, DOWN),
    ((1, 0),
     (1, 1)): (UP, RIGHT),
    ((1, 1),
     (0, 0)): (LEFT, RIGHT),
    ((1, 1),
     (0, 1)): (LEFT, DOWN),
    ((1, 1),
     (1, 0)): (RIGHT, DOWN),
    ((1, 1),
     (1, 1)): (HERE, HERE),
}  # type: Dict[Tuple[Vector2D, Vector2D], Tuple[Vector2D, ...]]


def sum_vectors(v1: Vector2D, v2: Vector2D) -> Vector2D:
    """
    >>> v1 = (-1, 2)
    >>> v2 = (3.0, -10)
    >>> sum_vectors(v1, v2)
    (2.0, -8)
    """
    return (v1[0] + v2[0], v1[1] + v2[1])


def scalar(vector: Vector2D, amount: float) -> Vector2D:
    return vector[0] * amount, vector[1] * amount


class VertexBoxes:
    """Eases the manipulation of a vertex and near squared 2x2 boxes group.
    """
    def __init__(self, map_: 'BlocksMap', xy: Vertex2D) -> None:
        self.map = map_
        self.x, self.y = xy
        bx, by = self.map.map_vertex(xy)

        self.boxes = NearBoxes(
            upleft=(bx - 1, by - 1), upright=(bx, by - 1),  # the 2 upper boxes
            downleft=(bx - 1, by), downright=(bx, by),  # the 2 lower boxes
        )
        self.upper_boxes = self.boxes.upleft, self.boxes.upright
        self.right_boxes = self.boxes.upright, self.boxes.downright
        self.lower_boxes = self.boxes.downright, self.boxes.downleft
        self.left_boxes = self.boxes.upleft, self.boxes.downleft

        # 2 x 2 matrix cotaining box values relative to the vertex (usable for __repr__)
        self.block_matrix = (
            (self.map.get(self.boxes.upleft, 0), self.map.get(self.boxes.upright, 0)),
            (self.map.get(self.boxes.downleft, 0), self.map.get(self.boxes.downright, 0)),
        )


def remove_internal_edge_points(vertices: List[Vertex2D]) -> List[Vertex2D]:
    """
    Leave only the points that are in the corners.

    >>> points = [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 3), (-2, 3), (-3, 3)]
    >>> remove_internal_edge_points(points)
    [(0, 0), (0, 3), (-3, 3)]
    """
    ret = [vertices[0]]
    for i in range(1, len(vertices) - 1):
        triple = vertices[i - 1: i + 2]
        diff = np.diff(triple, axis=0)
        if tuple(diff[0]) != tuple(diff[1]):
            # the 3 vertices don't form a line, so get the median one
            ret.append(vertices[i])

    ret.append(vertices[-1])
    return ret


def normalized_perimeter(wall_perimeter: WallPerimeter) -> WallPerimeter:
    """
    Normalize wall perimeter to make it start from topleft.

    >>> normalized_perimeter([(1, 0), (1, 1), (0, 1), (0, 0), (1, 0)])
    [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    """
    minimum = min(wall_perimeter)
    # Remove duplicates preserving order:
    wall_perimeter = list(OrderedDict.fromkeys(wall_perimeter))
    deq = deque(wall_perimeter)  # use deque just to use the rotate (circular shift)
    while deq[0] != minimum:
        deq.rotate(1)
    # The last item must be equal to the first by convention.
    deq.append(deq[0])
    return list(deq)


class BlocksMap(dict):

    def __init__(self, data: Mapping, map_size: Tuple[int, int], box_size: int=1) -> None:
        super().__init__(data)
        self.map = data
        self.map_size = map_size
        self.box_size = box_size

    def get_grid_vertices(self) -> Iterable[Vertex2D]:
        """Returns an iterator for all map virtual "grid" vertices,
        so regardless they are part of wall or not.
        """
        width, height = self.map_size
        for by in range(height):
            for bx in range(width):
                x = bx * self.box_size
                y = by * self.box_size
                yield (x, y)

    def map_vertex(self, xy: Vertex2D) -> Pos:
        """Given a vertex position, returns the map box whose the
        vertex is the top-left one.
        """
        x, y = xy
        return int(x / self.box_size), int(y / self.box_size)

    def vertex2boxes(self, xy: Vertex2D) -> VertexBoxes:
        """Returns the 4 neighbour map boxes (white or not)
        which share the same given vertex.
        """
        # get the box whose the vertex is the top-left
        return VertexBoxes(self, xy)

    def get_next_block_vertices(self, vertex: Vertex2D) -> List[Vertex2D]:
        """Returns neighbour vertices which are actually block edges or vertices
        (i.e. contiguous to map walls, so not free space vertices).
        """
        ret = []  # type: List[Vertex2D]
        v_boxes = self.vertex2boxes(vertex)
        versors = POSSIBLE_DIRECTIONS[v_boxes.block_matrix]
        #ret = [tuple(vertex + np.array(v)) for v in versors]
        ret = [sum_vectors(vertex, v) for v in versors]
        #ret = [v for v in versors]
        return ret

    def vertex2blocks(self, xy: Vertex2D) -> List[VertexBoxes]:
        return [box for box in self.vertex2boxes(xy).boxes if box in self.map]

    def is_border_vertex(self, vertex: Vertex2D) -> bool:
        """Returns True if the vertex is part of an edge or is a corner.
        Returns false if the vertex is inner a wall or outside.
        """
        v_blocks = self.vertex2blocks(vertex)
        return 0 < len(v_blocks) < 4

    def build(self) -> List[List[Vertex2D]]:
        ret = []  # type: List[WallPerimeter]
        tracked_vertices = []
        tracked_blocks = set()
        if not self.map:
            return []

        for vertex in self.get_grid_vertices():  # FIXME: not block but box
            if not self.is_border_vertex(vertex):
                continue

            if vertex in tracked_vertices:
                continue

            # start new wall perimeter from this disjointed block
            wall_perimeter = []

            # is this vertex already tracked?
            near_blocks = self.vertex2blocks(vertex)
            if len(near_blocks) == 4:
                continue

            first_vertex = vertex
            tracked = [vertex]
            old_versor = (0.0, 0.0)  # like a `None` but supporting the array sum
            wall_perimeter.append(vertex)
            closable = False
            while True:
                logging.debug('Vertex: {}'.format(vertex))

                # mark near clocks as "done"
                tracked_blocks = tracked_blocks.union(self.vertex2boxes(vertex).boxes)
                tracked_vertices.append(vertex)

                vertices = self.get_next_block_vertices(vertex)
                # Cycle through new possible vertices to explore
                for v_next in vertices:
                    versor_next = sum_vectors(v_next, scalar(tracked[-1], -1))
                    logging.debug('Exploring {} -> {}'.format(VERSOR_NAME[versor_next], v_next))

                    # Avoid to go back
                    if not(np.array(old_versor) + np.array(versor_next)).any():
                        logging.debug('Do not go just back to {}'.format(v_next))
                        continue

                    if v_next not in tracked:
                        logging.debug('Found new vertex to go: {}'.format(v_next))
                        wall_perimeter.append(v_next)
                        break
                    else:
                        if v_next == wall_perimeter[0]:
                            # could close the polygon
                            closable = True
                        logging.debug('{} in tracked {}'.format(v_next, tracked))

                if v_next in tracked:
                    if closable:
                        logging.debug('Closing the polygon')
                        wall_perimeter.append(first_vertex)
                    break

                versor = sum_vectors(v_next, scalar(tracked[-1], -1))
                versor_name = VERSOR_NAME[versor]
                tracked.append(v_next)

                if versor != old_versor:
                    logging.debug('changed versor')
                else:
                    logging.debug('same versor')
                logging.debug('going {}'.format(versor_name))

                vertex = v_next
                old_versor = versor

                logging.debug(str(wall_perimeter))
            # find new contiguous free position to move vertex to
            logging.debug(str(tracked))
            wall_perimeter = remove_internal_edge_points(wall_perimeter)
            wall_perimeter = normalized_perimeter(wall_perimeter)
            ret.append(wall_perimeter)

        ret.sort()
        return ret


map_sample = BlocksMap({
    (1, 1): 1, (2, 1): 1
}, map_size=(3, 3))


def mat2map(matrix: Iterable[Iterable[int]]) -> BlocksMap:
    """Create a block map.
    """
    ret = {}
    for y, row in enumerate(matrix):
        for x, walkable in enumerate(row):
            if not walkable:
                ret[(x, y)] = 1
    return BlocksMap(ret, map_size=(x + 1, y + 1))


def load_png(filepath: str) -> WalkableMatrix:
    ret = []
    img = Image.open(filepath)
    for y in range(img.height):
        row = []
        for x in range(img.width):
            pixel = img.getpixel((x, y))
            alpha = pixel[-1] if img.mode == 'RGBA' else 255
            walkable = alpha == 0 or pixel[:3] == (255, 255, 255)
            row.append(int(walkable))
        ret.append(row)
    return ret
