"""
Test suite for the rectangle tessellation.
"""
import turtle_utils as tu
import pytest


TEST_CASES = [
    {
        'name': '1x1square',
        'description': 'A simple 1x1 square should be tessellated by a single square face.',
        'vertices': [(0, 0), (1, 0), (1, 1), (0, 1)],
        'perimeter': [0, 1, 2, 3],
        'expected': [(0, 1, 2, 3)],
    },
    {
        'name': '5x2rect',
        'description': 'A 5x2 rectangle should be tessellated by a single rectangle.',
        'vertices': [(0, 0), (5, 0), (5, 2), (0, 2)],
        'perimeter': [0, 1, 2, 3],
        'expected': [(0, 1, 2, 3)]
    },
    {
        'name': 'L',
        'description': 'A L-shaped polygon should be tessellated by 3 rectangles (2 non-corner vertices added).',
        'vertices': [
            (0, 0), (1, 0), (1, 3), (2, 3), (2, 4), (0, 4),
            (0, 3), (1, 4),  # non-corner vertices
        ],
        'perimeter': [0, 1, 2, 3, 4, 5],
        'expected': [(0, 1, 2, 6), (2, 3, 4, 7), (6, 2, 7, 5)],
    },
    {
        'name': 'C',
        'description': 'A C-shaped polygon should be tessellated by 5 rectangles.',
        'vertices': [
            (0, 0),  # top-left
            (1, 0),  # non-corner
            (2, 0),  # top-right
            (2, 1), (1, 1),
            (1, 2), (2, 2),
            (2, 3),
            (1, 3),  # non-corner
            (0, 3),
            (0, 2), (0, 1),  # non-corner
        ],
        'perimeter': [0, 2, 3, 4, 5, 6, 7, 9],
        'expected': [
            (0, 1, 4, 11), (1, 2, 3, 4),
            (11, 4, 5, 10),
            (10, 5, 8, 9), (5, 6, 7, 8),
        ],
    },
    {
        'name': 'Z',
        'description': 'A Z-shaped polygon should be tassellated by 5 rectangles.',
        'vertices': [
            (0, 0), (1, 0), (2, 0),
            (2, 1), (3, 1), (3, 2),
            (2, 2), (1, 2), (1, 1),
            (0, 1),
        ],
        'perimeter': [0, 2, 3, 4, 5, 7, 8, 9],
        'expected': [
            (0, 1, 8, 9), (1, 2, 3, 8),
            (3, 4, 5, 6), (8, 3, 6, 7),
        ],
    },
    {
        'name': 'T',
        'description': 'A T-shape polygon should be tessellated by 5 rectangles',
        'vertices': [
            (-1, 0),  # [0] top-left vertex
            (0, 0), (1, 0),  # [1, 2] non-corner vertices
            (2, 0),  # [3] top-right vertex
            (2, -1), (1, -1),  # [4, 5]
            (1, -3), (0, -3),  # [6, 7] lowest vertices
            (0, -1), (-1, -1),  # [8, 9]
        ],
        'perimeter': [0, 3, 4, 5, 6, 7, 8, 9],
        'expected': [
            (0, 1, 8, 9), (1, 2, 5, 8), (2, 3, 4, 5),
            (8, 5, 6, 7),  # vertical part
        ],
    },
    {
        'name': '3x3cross',
        'description': 'A "+"-shaped polygon should be tessellated by 5 rectangles.',
        'vertices': [
            (+0, 0), (+1, 0), (1, 1),  # up
            (+2, 1), (+2, 2), (1, 2),  # right
            (+1, 3), (+0, 3), (0, 2),  # down
            (-1, 2), (-1, 1), (0, 1),  # left
        ],
        'perimeter': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        'expected': [
            (0, 1, 2, 11), (2, 3, 4, 5), (5, 6, 7, 8), (8, 9, 10, 11),
            (11, 2, 5, 8),  # central square
        ],
    },
    {
        'name': 'O',
        'description': 'A O-shaped wall has 2 perimeters and should be tessellated by 8 polygons.',
        'vertices': [
            (0, 0), (1, 0), (2, 0), (3, 0),
            (3, 1), (3, 2), (3, 3),
            (3, 2), (3, 1), (3, 0),
            (2, 0), (1, 0),
            (1, 1), (2, 1), (2, 2), (1, 2),  # inner square
        ],
        'perimeter': [],
        'expected': [
            (0, 1, 12, 11), (2, 3, 13, 12), (3, 4, 5, 13),
        ]
    }
]


def get_polygon(vertices, indices):
    return [vertices[i] for i in vertices]


@pytest.mark.skip('blender will cover the walls')
@pytest.mark.parametrize('case', TEST_CASES, ids=lambda s: s['description'])
def test_cover(case):
    polygon = [case['vertices'][i] for i in case['perimeter']]
    if polygon:
        tu.draw_polygon(polygon, zoom=60, speed=3)
    for face in case['expected']:
        tu.draw_polygon([case['vertices'][i] for i in face], zoom=60, speed=3, color=tu.get_random_color())
    tu.clear()

