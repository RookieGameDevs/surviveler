#!/usr/bin/env python

from client import Client
from configparser import ConfigParser
from connection import Connection
from contextlib import ContextDecorator
from message import MessageProxy
from renderer import Renderer
import logging
import os
import sdl2 as sdl


LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

LOG = logging.getLogger(__name__)


CONFIG_FILE = os.path.join(os.getcwd(), 'client.ini')


def setup_logging(config):
    """Setups the logging module

    :param config: the logging section of the config object
    :type config: instance of :class:`configparser.SectionProxy`
    """
    numeric_level = getattr(logging, config['Level'], None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % LOG_LEVEL)
    logging.basicConfig(
        level=numeric_level,
        format='[%(asctime)s - %(levelname)s:%(name)s] %(msg)s')


class sdl2context(ContextDecorator):
    def __enter__(self):
        LOG.debug('Creating SDL context')
        sdl.SDL_Init(sdl.SDL_INIT_VIDEO)
        return self

    def __exit__(self, *exc):
        LOG.debug('Quitting SDL context')
        sdl.SDL_Quit()
        return False


@sdl2context()
def main(config):
    renderer = Renderer(config['Renderer'])
    conn = Connection(config['Network'])
    proxy = MessageProxy(conn)
    client = Client(renderer, proxy)
    client.start()
    renderer.shutdown()


if __name__ == '__main__':
    config = ConfigParser()
    config.read(CONFIG_FILE)

    setup_logging(config['Logging'])

    LOG.debug('Loaded config file {}'.format(CONFIG_FILE))
    main(config)
