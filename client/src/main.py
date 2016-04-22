#!/usr/bin/env python

from client import Client
from client import sdl2context
from configparser import ConfigParser
from connection import Connection
import os


CONFIG_FILE = os.path.join(os.getcwd(), 'client.ini')


@sdl2context()
def main(config):
    conn = Connection(config)
    client = Client(1024, 768, conn)
    client.start()
    client.quit()


if __name__ == '__main__':
    config = ConfigParser()
    config.read(CONFIG_FILE)
    main(config)
