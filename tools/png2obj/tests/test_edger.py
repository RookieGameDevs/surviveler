from ..png2obj import load_png
from ..png2obj import mat2map
import os
import pytest


TEST_DIRPATH = os.path.dirname(__file__)
SAMPLES_DIRPATH = os.path.join(TEST_DIRPATH, 'samples')

EXAMPLES = [
    # Single paths
    {
        'name': 'empty1x1',
        'matrix': [[1]],
        'vertices':[],
    },
    {
        'name': 'empty3x3',
        'matrix': [
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1],
        ],
        'vertices':[],
    },
    {
        'name': 'full1x1',
        'matrix': [[0]],
        'vertices': [
            [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
        ],
    },
    {
        'name': 'full2x2',
        'matrix': [
            [0, 0],
            [0, 0],
        ],
        'vertices': [
            [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
        ],
    },
    {
        'name': 'full3x3',
        'matrix': [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        'vertices': [
            [(0, 0), (3, 0), (3, 3), (0, 3), (0, 0)],
        ],
    },
    {
        'name': 'square1x1',
        'matrix': [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        'vertices': [
            [(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)],
        ],
    },
    {
        'name': 'rect2x1',
        'matrix': [
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1],
        ],
        'vertices': [
            [(1, 1), (3, 1), (3, 2), (1, 2), (1, 1)],
        ]
    },
    {
        'name': 'rect1x2',
        'matrix': [
            [1, 0, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 1, 1],
        ],
        'vertices': [
            [(1, 0), (2, 0), (2, 2), (1, 2), (1, 0)],
        ]
    },
    {
        'name': 'L1x1',
        'matrix': [
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 1, 1],
        ],
        'vertices': [
            [(1, 1), (3, 1), (3, 2), (2, 2), (2, 3), (1, 3), (1, 1)],
        ],
    },
    {
        'name': 'square2x2',
        'matrix': [
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1],
        ],
        'vertices': [
            [(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)],
        ],
    },
    {
        'name': 'square3x3',
        'matrix': [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1],
        ],
        'vertices': [
            [(1, 1), (4, 1), (4, 4), (1, 4), (1, 1)],
        ],
    },
    {
        'name': 'snake',
        'matrix': [
            [0, 1, 1],
            [0, 0, 1],
            [1, 0, 1],
        ],
        'vertices': [
            [(0, 0), (1, 0), (1, 1), (2, 1), (2, 3), (1, 3), (1, 2), (0, 2), (0, 0)],
        ],
    },
    {
        'name': 'H',
        'matrix': [
            [0, 1, 0],
            [0, 0, 0],
            [0, 1, 0],
        ],
        'vertices': [
            [(0, 0), (1, 0), (1, 1), (2, 1), (2, 0), (3, 0),  # top-left to top-right
             (3, 3), (2, 3), (2, 2), (1, 2), (1, 3), (0, 3), (0, 0)],
        ],
    },
    {
        'name': 'T',
        'matrix': [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 0, 1, 1],
            [1, 1, 0, 1, 1],
            [1, 1, 1, 1, 1],
        ],
        'vertices': [
            [(1, 1), (4, 1), (4, 2), (3, 2), (3, 4), (2, 4), (2, 2), (1, 2), (1, 1)],
        ]
    },
    # Multiple paths
    {
        'name': '4blocks',
        'matrix': [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ],
        'vertices': [
            [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
            [(2, 0), (3, 0), (3, 1), (2, 1), (2, 0)],
            [(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)],
            [(0, 2), (1, 2), (1, 3), (0, 3), (0, 2)],
        ]
    },
    {
        'name': 'o_room_1x1',
        'matrix': [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 1, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1],
        ],
        'vertices': [
            [(1, 1), (4, 1), (4, 4), (1, 4), (1, 1)],
            [(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)],
        ],
    },
    {
        'name': 'o_room_1x1_bold',
        'matrix': [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        'vertices': [
            [(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)],
            [(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)],
        ],
    },
    {
        'name': 'o_room_2x2',
        'matrix': [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        'vertices': [
            [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)],
            [(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)],
        ],
    },
]


@pytest.mark.parametrize('case', EXAMPLES, ids=lambda s: s['name'])
def test_detect_edges(case: dict) -> None:
    matrix = case['matrix']
    blocks_map = mat2map(matrix)
    expected = sorted(case['vertices'])
    actual = sorted(blocks_map.build())
    assert actual == expected


@pytest.mark.parametrize('case', EXAMPLES, ids=lambda s: s['name'])
def test_png2matrix(case: dict) -> None:
    filename = case['name'] + '.png'
    filepath = os.path.join(SAMPLES_DIRPATH, filename)
    if not os.path.exists(filepath):
        pytest.skip('"{}" does not exist'.format(filepath))
    else:
        assert load_png(filepath) == case['matrix']
