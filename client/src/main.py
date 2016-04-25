#!/usr/bin/env python

from client import Client
from configparser import ConfigParser
from connection import Connection
from contextlib import ContextDecorator
from renderer import Renderer
import os
import sdl2 as sdl


CONFIG_FILE = os.path.join(os.getcwd(), 'client.ini')


class sdl2context(ContextDecorator):
    def __enter__(self):
        sdl.SDL_Init(sdl.SDL_INIT_VIDEO)
        return self

    def __exit__(self, *exc):
        sdl.SDL_Quit()
        return False


@sdl2context()
def main(config):
    renderer = Renderer(config['Renderer'])
    conn = Connection(config['Network'])
    client = Client(renderer, conn)
    client.start()
    renderer.shutdown()


if __name__ == '__main__':
    config = ConfigParser()
    config.read(CONFIG_FILE)
    main(config)
