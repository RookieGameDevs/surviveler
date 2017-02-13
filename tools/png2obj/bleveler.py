# -*- coding: utf-8 -*-
"""
Add-on to create level mesh based on png.

Main module to create a Wavefront obj file from a png one.

Involved steps:
    1 - convert a png to a walkable matrix;
    2 - find wall perimeters -> list of 2D edges;
    3 - extrude vertically the wall perimeters -> list of 3D faces;
    4 - fill top horizontal wall faces.

Python-3 only due to the type hinting (and 'super') syntax.

Glossary (to try to make some clearness):
    * cell - an element in the walkable matrix, with coordinates (x, y)
    * block - a non-walkable cell
    * vertex - a 2/3D point in a 2/3D space (used to describe wall perimeters and meshes)
    * wall perimeter - a 2D closed planar (z=0) polygon which corresponds to the wall borders
        (from a "top" view perspective).
        If the wall is open, you have 1 perimeter for 1 wall.
        If the wall is closed, you have an internal wall perimeter and an external one.
        Each png or level may consists of several separated walls.
"""
from collections import Counter
from collections import OrderedDict
from collections import deque
from collections import namedtuple
from typing import Dict  # noqa
from typing import Iterable
from typing import List
from typing import Mapping
from typing import NamedTuple
from typing import Set  # noqa
from typing import Tuple
import turtle as logo

# Blender stuff
import bpy
from bpy.props import StringProperty
from bpy_extras import image_utils


Pos = Tuple[int, int]
Versor2D = Tuple[int, int]
Vertex2D = Tuple[float, float]
Vector2D = Vertex2D
Vertex3D = Tuple[float, float, float]
Triangle2D = Tuple[Vertex2D, Vertex2D, Vertex2D]
Triangle3D = Tuple[Vertex3D, Vertex3D, Vertex3D]
WallPerimeter = List[Vertex2D]
WalkableMatrix = List[List[int]]
VertexCells = NamedTuple('NearCells',
    [
        ('upleft', Pos),
        ('upright', Pos),
        ('downright', Pos),
        ('downleft', Pos),
    ]
)


Cell = namedtuple('Cell', ['x', 'y'])
NearVertices = namedtuple('NearVertices', ['left', 'up', 'right', 'down'])


LEFT = (-1, 0)
UP = (0, -1)
RIGHT = (1, 0)
DOWN = (0, 1)
HERE = (0, 0)
STILL = (0, 0)
VERSOR_NAME = {
    LEFT: 'left', UP: 'up', RIGHT: 'right', DOWN: 'down', HERE: 'here'
}  # type: Dict[Vector2D, str]

# Angles for the turtle
ANGLES = {LEFT: 270, UP: 0, RIGHT: 90, DOWN: 180}  # type: Dict[Vertex2D, int]


# Each vertex has 4 neighbour cells, and each cell can be walkable or not (block).
# This map represents every case with relative "mouvement" possibility
# of a vertex to track the wall perimeter.

RULES = {
    ((0, 0),
     (0, 0)): {},
    ((0, 0),
     (0, 1)): {STILL: RIGHT, UP: RIGHT, LEFT: DOWN},
    ((0, 0),
     (1, 0)): {STILL: DOWN, UP: LEFT, RIGHT: DOWN},
    ((0, 0),
     (1, 1)): {STILL: RIGHT, RIGHT: RIGHT, LEFT: LEFT},
    ((0, 1),
     (0, 0)): {STILL: UP, LEFT: UP, DOWN: RIGHT},
    ((0, 1),
     (0, 1)): {STILL: UP, UP: UP, DOWN: DOWN},
    ((0, 1),
     (1, 0)): {STILL: RIGHT, UP: RIGHT, LEFT: DOWN, RIGHT: UP, DOWN: LEFT},
    ((0, 1),
     (1, 1)): {STILL: UP, RIGHT: UP, DOWN: LEFT},
    ((1, 0),
     (0, 0)): {STILL: LEFT, RIGHT: UP, DOWN: LEFT},
    ((1, 0),
     (0, 1)): {STILL: RIGHT, UP: LEFT, DOWN: RIGHT, LEFT: UP, RIGHT: DOWN},
    ((1, 0),
     (1, 0)): {STILL: UP, UP: UP, DOWN: DOWN},
    ((1, 0),
     (1, 1)): {STILL: RIGHT, LEFT: UP, DOWN: RIGHT},
    ((1, 1),
     (0, 0)): {STILL: RIGHT, LEFT: LEFT, RIGHT: RIGHT},
    ((1, 1),
     (0, 1)): {STILL: LEFT, UP: LEFT, RIGHT: DOWN},
    ((1, 1),
     (1, 0)): {STILL: RIGHT, UP: RIGHT, LEFT: DOWN},
    ((1, 1),
     (1, 1)): {},
}  # type: Dict[Tuple[Vector2D, Vector2D], Dict[Versor2D, Versor2D]]


DRAW_SIZE = 300


def sum_vectors(v1: Vector2D, v2: Vector2D) -> Vector2D:
    """Sums 2 bi-dimensional vectors.

    >>> v1 = (-1, 2)
    >>> v2 = (3.0, -10)
    >>> sum_vectors(v1, v2)
    (2.0, -8)
    """
    return (v1[0] + v2[0], v1[1] + v2[1])


def remove_internal_edge_points(vertices: List[Vertex2D]) -> List[Vertex2D]:
    """
    Leaves only the points that are in the corners.

    >>> points = [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 3), (-2, 3), (-3, 3)]
    >>> remove_internal_edge_points(points)
    [(0, 0), (0, 3), (-3, 3)]
    """
    ret = [vertices[0]]
    for i in range(1, len(vertices) - 1):
        # Make the diff of 3 current contiguous vertices
        dx1 = vertices[i][0] - vertices[i - 1][0]
        dy1 = vertices[i][1] - vertices[i - 1][1]
        dx2 = vertices[i + 1][0] - vertices[i][0]
        dy2 = vertices[i + 1][1] - vertices[i][1]
        # If the 2 diffs are not equal:
        if (dx1 != dx2) or (dy1 != dy2):
            # the 3 vertices don't form a line, so get the median one
            ret.append(vertices[i])

    ret.append(vertices[-1])
    return ret


def remove_contiguous_values(lst: List[Tuple[float, float]]) -> None:
    """
    >>> lst = [1, 2, 8, 8, 8, 0, 0, 5]
    >>> remove_contiguous_values(lst)
    >>> lst
    [1, 2, 8, 0, 5]
    """
    i = 0
    while i < len(lst) - 1:
        if lst[i] == lst[i + 1]:
            del lst[i]
        else:
            i += 1


def normalized_perimeter(wall_perimeter: WallPerimeter) -> WallPerimeter:
    """
    Normalizes the wall perimeter to make it start from its topleft.

    >>> normalized_perimeter([(1, 0), (1, 1), (0, 1), (0, 0), (1, 0)])
    [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    """
    minimum = min(wall_perimeter)
    deq = deque(wall_perimeter)  # use deque just to use the rotate (circular shift)
    while deq[0] != minimum:
        deq.rotate(1)
    # The last item must be equal to the first by convention.
    deq.append(deq[0])
    ret = list(deq)
    # Remove contiguous duplicates, preserving order.
    remove_contiguous_values(ret)
    return ret


def list_to_index_map(the_list: list) -> OrderedDict:
    ret = OrderedDict()
    assert len(set(the_list)) == len(the_list), 'Error: the list contains duplicated elements'
    for i, element in enumerate(the_list):
        ret[element] = i
    return ret


def wall_perimeters_to_verts_edges(wall_perimeters: List[WallPerimeter]) -> Tuple[List[Vertex2D], List[Tuple[int, int]]]:
    """
    Return a (a, b) tuple in which:
    * a -- unique vertices
    * b -- list of vertex indices couples

    >>> verts, edges = wall_perimeters_to_verts_edges([[(0, 0), (3, 0), (3, 1), (0, 1)], [(3, 1), (4, 1), (4, 2), (3, 2)]])
    >>> len(verts)
    7
    >>> verts.count((3, 1))
    1
    >>> verts
    [(0, 0), (3, 0), (3, 1), (0, 1), (4, 1), (4, 2), (3, 2)]
    >>> edges
    [(0, 1), (1, 2), (2, 3), (3, 0), (2, 4), (4, 5), (5, 6), (6, 2)]
    """
    # TODO: speed-up with dict for vertex indices
    verts = []
    edges = []

    for wall in wall_perimeters:
        for vertex in wall:
            if vertex not in verts:
                verts.append(vertex)

    for iw, wall in enumerate(wall_perimeters):
        for i in range(0, len(wall) - 1):
            vertex_i = wall[i]
            vertex_i1 = wall[i + 1]
            edges.append((verts.index(vertex_i), verts.index(vertex_i1)))

    return verts, edges


def add_3D(vertices: List[Vertex2D], z: float=0):
    return [(v[0], v[1], z) for v in vertices]


def build_walls(walls_map: Mapping, map_size: Tuple[int, int], cell_size: int=1, turtle=False) -> List[List[Vertex2D]]:
    """
    Main function (edge detection): builds the list of wall perimeters.

    TODO: Use a walkable matrix instead of walls_map.
    """

    def get_grid_vertices() -> Iterable[Vertex2D]:
        """Returns an iterator for all map virtual "grid" vertices,
        so regardless they are part of a wall or not.
        """
        width, height = map_size
        for bx in range(width):
            for by in range(height):
                x = bx * cell_size
                y = by * cell_size
                yield (x, y)

    def map_vertex(xy: Vertex2D) -> Pos:
        """Given a vertex position, returns the map cell whose the
        vertex is the top-left one.
        """
        x, y = xy
        return int(x / cell_size), int(y / cell_size)

    def vertex2cells(xy: Vertex2D) -> VertexCells:
        """Returns the 4 neighbour map cells (white or not)
        which share the same given vertex.
        """
        bx, by = map_vertex(xy)
        return VertexCells(upleft=(bx - 1, by - 1), upright=(bx, by - 1), downleft=(bx - 1, by), downright=(bx, by))

    def cells2block_matrix(cells: VertexCells) -> Tuple[Pos, Pos]:
        """Given 4 vertex cells, returns a 2x2 tuple with walkable/non-walkable info.
        """
        return ((walls_map.get(cells.upleft, 0), walls_map.get(cells.upright, 0)), (walls_map.get(cells.downleft, 0), walls_map.get(cells.downright, 0)))

    ret = []  # type: List[WallPerimeter]

    if turtle:
        logo.mode('logo')
        logo.speed(11)
        drawsize = int(DRAW_SIZE / (1 + max(map(max, walls_map)))) if walls_map else 0  # type: ignore

    if not walls_map:
        return []

    tracked_vertices = Counter()  # type: Dict[Vertex2D, int]

    for iv, vertex in enumerate(get_grid_vertices()):
        v_cells = vertex2cells(vertex)
        blocks_matrix = cells2block_matrix(v_cells)
        versors = RULES[blocks_matrix]
        n_versors = len(versors) - 1  # remove still
        if n_versors == -1:
            # not a border verdex
            # inside 4 blocks or 4 empty cells
            continue

        n_passes = tracked_vertices[vertex]
        if n_versors == 4:
            # should pass by here exactly 2 times
            if n_passes > 1:
                continue

        elif n_passes > 0:
            continue

        # start new wall perimeter from this disjointed block
        wall_perimeter = []

        first_vertex = vertex
        old_versor = (0, 0)  # like a `None` but supporting the array sum
        versor = old_versor
        wall_perimeter.append(vertex)
        wall_vertex = vertex

        if turtle:
            logo.penup()
            logo.setpos(wall_vertex[0] * drawsize - drawsize, -wall_vertex[1] * drawsize + drawsize)
            logo.pendown()

        while True:
            v_cells = vertex2cells(wall_vertex)
            blocks_matrix = cells2block_matrix(v_cells)
            versors = RULES[blocks_matrix]

            # Trick to handle the "chessboard" case.
            tracked_vertices[wall_vertex] += (1 if len(versors) == 5 else 2)

            versor_next = versors[versor]
            v_next = sum_vectors(wall_vertex, versor_next)
            wall_perimeter.append(v_next)

            old_versor = versor
            versor = versor_next
            wall_vertex = wall_perimeter[-1]

            if turtle:
                logo.setheading(ANGLES[versor_next])
                logo.fd(drawsize)

            if wall_vertex == first_vertex:
                break

        wall_perimeter = remove_internal_edge_points(wall_perimeter)
        wall_perimeter = normalized_perimeter(wall_perimeter)
        ret.append(wall_perimeter)

    ret.sort()
    return ret


def mat2map(matrix: WalkableMatrix, wall=1) -> Mapping:
    """Creates a blocks map from a walkable matrix.
    """
    ret = {}
    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            if value == wall:
                ret[(x, y)] = 1
    return ret, (x + 1, y + 1)


def bpy_png2matrix(filepath: str) -> WalkableMatrix:
    ret = []
    img = image_utils.load_image(filepath)
    assert img.channels == 4, 'Only images with alpha channels are supported (so far)!'
    ipx = 0
    width, height = img.size
    pixels = img.pixels
    for y in range(height):
        row = []
        for x in range(width):
            color = pixels[ipx: ipx + 3]
            alpha = pixels[ipx + 3]  # remove '.'
            walkable = (alpha == 0 or color == (1, 1, 1))
            # 1 => obstacle
            row.append(int(not walkable))
            ipx += 4
        ret.append(row)
    return ret


bl_info = {
    'name': 'png2obj',
    'category': 'Import-Export',
    'author': 'Iacopo Marmorini <iacopomarmorini@gmail.com>',
    'version': (1, 0),
    'blender': (2, 7, 8),
    'location': 'View3D > Object > Move4 Object',
    'description': 'Create a mesh from a bitmap',
    'warning': 'alpha',
    'wiki_url': '',
    'tracker_url': '',
}


bpy.types.Scene.ImagePath = StringProperty(name='Image file',
    attr='custompath',  # this a variable that will set or get from the scene
    description='The image to use to generate the level',
    maxlen=1024,
    subtype='FILE_PATH',
    default='')  # this set the text


class VIEW3D_PT_custompathmenupanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Surviveler level generator'

    def draw(self, context):
        self.layout.label(text='Select png to use as level base')  # Text above the button

        self.layout.prop(context.scene, 'ImagePath')

        # operator button
        # OBJECT_OT_CustomButton => object.CustomButton
        self.layout.operator('object.custombutton')


class OBJECT_OT_custombutton(bpy.types.Operator):
    bl_idname = 'object.custombutton'
    bl_label = 'Generate'
    __doc__ = 'It will load the image and create the level mesh from the file.'

    def invoke(self, context, event):
        wall_height = 3  # TODO: parametrize from GUI

        file_path = context.scene.ImagePath
        matrix = bpy_png2matrix(file_path)
        blocks_map, map_size = mat2map(matrix)

        print('Detecting edges...')
        wall_perimeters = sorted(build_walls(blocks_map, map_size=map_size, turtle=False))
        verts2D, edges = wall_perimeters_to_verts_edges(wall_perimeters)
        verts = add_3D(verts2D)
        faces = []
        print('Found {:,} vertices and {:,} edges'.format(len(verts), len(edges)))

        # ============== Example data ======================
        # verts = [
        #     (0, 0, 0), (2, 0, 0), (2, 1, 0), (0, 1, 0),
        #     (-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0),
        # ]
        # edges = [
        #     (0, 1), (1, 2), (2, 3), (3, 0),
        #     (4, 5), (5, 6), (6, 7), (7, 4),
        # ]

        mesh_data = bpy.data.meshes.new("cube_mesh_data")
        mesh_data.from_pydata(verts, edges, faces)
        mesh_data.update()

        obj = bpy.data.objects.new("Level", mesh_data)

        scene = bpy.context.scene
        scene.objects.link(obj)

        # select/active
        obj.select = True
        scene.objects.active = obj

        # Switch to edit mode
        bpy.ops.object.editmode_toggle()

        # Extrude vertically
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={'value': (0, 0, wall_height)})

        # Fill upper horizontal wall surfaces (triangulate)
        bpy.ops.mesh.fill()

        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(VIEW3D_PT_custompathmenupanel)
    bpy.utils.register_class(OBJECT_OT_custombutton)
    print('register')


def unregister():
    bpy.utils.register_class(VIEW3D_PT_custompathmenupanel)
    bpy.utils.register_class(OBJECT_OT_custombutton)
    print('unregister')

if __name__ == '__main__':
    register()
