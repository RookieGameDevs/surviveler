from sdl2.sdlmixer import MIX_DEFAULT_FORMAT
from sdl2.sdlmixer import Mix_GetError
from sdl2.sdlmixer import Mix_LoadWAV
from sdl2.sdlmixer import Mix_OpenAudio
from sdl2.sdlmixer import Mix_PlayChannel
from sdl2.ext.compat import byteify
import os


DATA_ROOT = '../data'
AUDIO_ROOT = os.path.join(DATA_ROOT, 'audio')
FX_ROOT = os.path.join(AUDIO_ROOT, 'fx')


# Setup

if Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 1024):
    raise RuntimeError(
        'Cannot open mixed audio: {}'.format(Mix_GetError()))


# Scan and preload sound effects

sounds = {}
for filename in os.listdir(FX_ROOT):
    name, ext = os.path.splitext(filename)
    filepath = os.path.join(FX_ROOT, filename)
    sounds[name] = Mix_LoadWAV(byteify(filepath, "utf-8"))


def play_fx(sound_name):
    channel = Mix_PlayChannel(-1, sounds[sound_name], 0)
    if channel == -1:
        raise RuntimeError("Cannot play sample: {}".format(Mix_GetError()))
