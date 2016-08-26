from PIL import Image
import numpy as np
import os
import sys


def load(image_path):
    image = Image.open(image_path)
    grayscale = image.convert('L')
    return np.array(grayscale)


def build_obj(arr, size=1):
    res = ['# Surviveler: bmp2obj.py']
    res.append('o Test')
    v_counter = 1
    vn = 1
    vertices = []
    faces = []
    for y, row in enumerate(arr):
        for x, value in enumerate(row):
            if value == 0:
                v1 = x * size, y * size, 0.0
                v2 = (x + 1) * size, y * size, 0.0
                v3 = x * size, (y + 1) * size, 0.0
                v4 = (x + 1) * size, (y + 1) * size, 0.0
                vertices.append('v {:.6f} {:.6f} {:.6f}'.format(*v1))
                vertices.append('v {:.6f} {:.6f} {:.6f}'.format(*v2))
                vertices.append('v {:.6f} {:.6f} {:.6f}'.format(*v3))
                vertices.append('v {:.6f} {:.6f} {:.6f}'.format(*v4))
                face = 'f {v1_i} {v2_i} {v3_i} {v4_i}'.format(
                    v1_i=v_counter, v2_i=v_counter + 1, v3_i=v_counter + 3, v4_i=v_counter + 2
                )
                faces.append(face)
                v_counter += 4
                vn += 1
    res.extend(vertices)
    res.append('s off')
    res.extend(faces)
    return '\n'.join(res)


def export_obj(obj, dst):
    with open(dst, 'w') as fp:
        fp.write(obj)
    return os.path.getsize(dst)


def main(image_filepath):
    arr = load(image_filepath)
    obj = build_obj(arr)
    print(export_obj(obj, 'test.obj'))


if __name__ == '__main__':
    main(sys.argv[1])
