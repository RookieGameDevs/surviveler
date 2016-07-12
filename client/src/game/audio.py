from sdl2.ext.compat import byteify
from sdl2.sdlmixer import MIX_DEFAULT_FORMAT
from sdl2.sdlmixer import Mix_GetError
from sdl2.sdlmixer import Mix_Init
from sdl2.sdlmixer import Mix_LoadMUS
from sdl2.sdlmixer import Mix_LoadWAV
from sdl2.sdlmixer import Mix_OpenAudio
from sdl2.sdlmixer import Mix_PlayChannel
from sdl2.sdlmixer import Mix_PlayMusic
from sdl2.sdlmixer import Mix_VolumeMusic
import os


DATA_ROOT = '../data'
AUDIO_ROOT = os.path.join(DATA_ROOT, 'audio')
MUSIC_ROOT = os.path.join(AUDIO_ROOT, 'music')
FX_ROOT = os.path.join(AUDIO_ROOT, 'fx')


# Audio setup

if Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 1024):
    raise RuntimeError(
        'Cannot open mixed audio: {}'.format(Mix_GetError()))

initted = Mix_Init(0)
if initted == -1:
    raise RuntimeError(
        'Cannot initialize mixer: {}'.format(Mix_GetError()))


# Scan and preload sound effects
sounds = {}
for filename in os.listdir(FX_ROOT):
    name, ext = os.path.splitext(filename)
    filepath = os.path.join(FX_ROOT, filename)
    sounds[name] = Mix_LoadWAV(byteify(filepath, 'utf-8'))

musics = {}
for filename in os.listdir(MUSIC_ROOT):
    name, ext = os.path.splitext(filename)
    filepath = os.path.join(MUSIC_ROOT, filename)
    # print(os.stat(filepath))
    print('Loading', filename)
    musics[name] = Mix_LoadMUS(byteify(filepath, 'utf-8'))
    if musics[name] is None:
        raise RuntimeError(
            'Cannot open audio file: {}'.format(Mix_GetError()))


# Audio API

def play_music(music_name, loops=-1, volume=None):
    """Play a soundtrack.

    :param: music_name: The music name (without extension).
    :type music_name: str

    :param loops: Number of times to play through the music.
                  -1 (default) plays the music forever.
    :type loops: int

    :param volume: Set music volume (0-127).
    :type volume: int.
    """
    if volume:
        Mix_VolumeMusic(volume)
    ret = Mix_PlayMusic(musics[music_name], loops)
    assert ret != -1, 'Cannot play music "{}"'.format(music_name)


def play_fx(sound_name, loops=1):
    """Plays a preloaded sound effect using the first available channel.

    :param: sound_name: The sound name (without extension).
    :type sound_name: str

    :param loops: Number of times to play through the sound.
    :type loops: int
    """
    channel = Mix_PlayChannel(-1, sounds[sound_name], loops)
    if channel == -1:
        raise RuntimeError('Cannot play sample: {}'.format(Mix_GetError()))
    print('Playing {} in channel {}'.format(sound_name, channel))
