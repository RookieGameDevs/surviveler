import turtle
import random


def clear():
    turtle.clear()


def get_random_color():
    return tuple([random.random(), random.random(), random.random()])


def draw_polygon(polygon, zoom=1, color=None, speed=None):
    if speed is not None:
        turtle.speed(speed)

    reset = turtle.pencolor()
    if color:
        turtle.pencolor(color)

    for i, vertex in enumerate(polygon + [polygon[0]]):
        if i == 0:
            turtle.up()
        elif i == 1:
            turtle.down()
        x, y = vertex
        turtle.setpos(x * zoom, y * zoom)

    if color:
        turtle.pencolor(reset)
