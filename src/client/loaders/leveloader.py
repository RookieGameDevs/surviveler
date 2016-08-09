"""Utility level loader to play with first levels.

Useful to load simple .txt formatted levels.
"""

import json


SEP = b'.'
WALKABLE = 1
NOT_WALKABLE = 0


def load_txt_level(file_path):
    """Loads a txt file and return a "walkability matrix" (list of lists)
    of the level.

    :rtype: list
    """
    res = []
    with open(file_path, 'rb') as fp:
        res = parse_txt_level(fp)
    return res


def parse_txt_level(lines):
    """Parses a lines iterable and returns a "walkability matrix".

    :rtype: list
    """
    res = []
    for line in lines:
        res.append([])
        for element in line.split(SEP):
            if element.strip():
                res[-1].append(NOT_WALKABLE)
            else:
                res[-1].append(WALKABLE)
    return res


def to_json(lev, file_path):
    """Exports walkability matrix to json.
    """
    with open(file_path, 'w') as fp:
        json.dump(lev, fp)


def convert_txt_level_to_json(file_path):
    lev = load_txt_level(file_path)
    to_json(lev, file_path + '.json')


TEST_STRING = b"""
*.*.*.*.*
*. . . .*
*.*. .*.*
"""


def test_parse():
    expected = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
    ]
    assert parse_txt_level(TEST_STRING.strip().splitlines()) == expected


if __name__ == '__main__':
    test_parse()
