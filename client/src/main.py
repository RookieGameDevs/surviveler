#!/usr/bin/env python

from client import Client
from configparser import ConfigParser
from contextlib import ContextDecorator
from core import InputManager
from functools import partial
from game.audio import AudioManager
from loaders import ResourceManager
from network import Connection
from network import MessageProxy
from renderer import Renderer
from sdl2 import sdlmixer
import click
import game.actions  # noqa
import logging
import os
import sdl2 as sdl


LOG = logging.getLogger(__name__)


CONFIG_FILE = os.path.join(os.getcwd(), 'client.ini')


def filter_modules(modules, record):
    """Filter function for log modules.

    If modules is not an empty string, we filter out every logger that is not in
    the specified modules.

    Except for the modules argument that is binded at runtime, the record
    parameter and the return value are compliant to the logging.Filter.filter
    API.

    :param modules: List of enabled modules
    :type modules: list
    """
    if not modules:
        return True
    else:
        path = record.name.split('.')
        for i in range(len(path)):
            if '.'.join(path[:i + 1]) in modules:
                return True
        return False


def setup_logging(config):
    """Setups the logging module

    :param config: the logging section of the config object
    :type config: :class:`configparser.SectionProxy`
    """
    modules = []
    filter_str = config.get('Modules')
    if filter_str:
        modules = list(map(lambda x: x.strip(), filter_str.split(',')))

    numeric_level = getattr(logging, config['Level'], None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % config['level'])

    # Configure the logging module
    logging.basicConfig(
        level=numeric_level,
        format='[%(asctime)s - %(levelname)s:%(name)s] %(msg)s')

    # Add the filter to all the handlers
    for handler in logging.root.handlers:
        handler.addFilter(partial(filter_modules, modules))


class sdl2context(ContextDecorator):

    def __enter__(self):
        LOG.debug('Creating SDL context')
        sdl.SDL_Init(sdl.SDL_INIT_VIDEO | sdl.SDL_INIT_AUDIO)

        LOG.debug('Initializing SDL mixer')
        if sdlmixer.Mix_OpenAudio(44100, sdlmixer.MIX_DEFAULT_FORMAT, 2, 1024):
            raise RuntimeError(
                'Cannot open mixed audio: {}'.format(sdlmixer.Mix_GetError()))

        if sdlmixer.Mix_Init(0) == -1:
            raise RuntimeError(
                'Cannot initialize mixer: {}'.format(sdlmixer.Mix_GetError()))

        return self

    def __exit__(self, *exc):
        LOG.debug('Quitting SDL mixer')
        sdlmixer.Mix_Quit()

        LOG.debug('Quitting SDL context')
        sdl.SDL_Quit()
        return False


@sdl2context()
def main(name, character, config):
    renderer = Renderer(config['Renderer'])
    conn = Connection(config['Network'])
    proxy = MessageProxy(conn)
    input_mgr = InputManager()
    res_mgr = ResourceManager(config['Game'])
    audio_mgr = AudioManager(config['Sound'])

    client = Client(
        name, character, renderer, proxy, input_mgr, res_mgr, audio_mgr, config)

    client.start()
    renderer.shutdown()


@click.command()
@click.argument(
    'player_name',
    default='John Doe')
@click.argument(
    'character',
    default='ivan')
def bootstrap(player_name, character):
    config = ConfigParser()
    config.read(CONFIG_FILE)
    setup_logging(config['Logging'])

    LOG.debug('Loaded config file {}'.format(CONFIG_FILE))

    main(player_name, character, config)


if __name__ == '__main__':
    bootstrap()
