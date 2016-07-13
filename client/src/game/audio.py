from sdl2.ext.compat import byteify
from sdl2.sdlmixer import Mix_GetError
from sdl2.sdlmixer import Mix_HaltChannel
from sdl2.sdlmixer import Mix_LoadMUS
from sdl2.sdlmixer import Mix_LoadWAV
from sdl2.sdlmixer import Mix_PlayChannel
from sdl2.sdlmixer import Mix_PlayMusic
from sdl2.sdlmixer import Mix_VolumeMusic
import logging
import os


LOG = logging.getLogger(__name__)


DATA_ROOT = '../data'
AUDIO_ROOT = os.path.join(DATA_ROOT, 'audio')
MUSIC_ROOT = os.path.join(AUDIO_ROOT, 'music')
FX_ROOT = os.path.join(AUDIO_ROOT, 'fx')


class AudioManager:
    """Audio manager.

    Wraps SDL_Mixer functionalites into an object, keeping track of the various
    sounds playing to give the caller a chance to play/stop effects when some
    event is occurring.
    """

    def __init__(self):
        """Constructor. """

        # FIXME: audio file loading should happen using the resource manager
        self.sounds = {}
        for filename in os.listdir(FX_ROOT):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(FX_ROOT, filename)
            self.sounds[name] = Mix_LoadWAV(byteify(filepath, 'utf-8'))

        self.musics = {}
        for filename in os.listdir(MUSIC_ROOT):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(MUSIC_ROOT, filename)
            self.musics[name] = Mix_LoadMUS(byteify(filepath, 'utf-8'))
            if self.musics[name] is None:
                raise RuntimeError(
                    'Cannot open audio file: {}'.format(Mix_GetError()))

        # Map of the fx currently playing (indexed by entity id)
        self.sound_map = {}

    def play_music(self, music_name, loops=-1, volume=None):
        """Play a soundtrack.

        :param: music_name: The music name (without extension).
        :type music_name: :class:`str`

        :param loops: Number of times to play through the music.
                    -1 (default) plays the music forever.
        :type loops: :class:`int`

        :param volume: Set music volume (0-127).
        :type volume: :class:`int`
        """
        if volume:
            Mix_VolumeMusic(volume)
        if Mix_PlayMusic(self.musics[music_name], loops) == -1:
            LOG.error('Cannot play music "{}"'.format(music_name))

    def play_fx(self, sound_name, loops=0, key=None):
        """Plays a preloaded sound effect using the first available channel.

        :param: sound_name: The sound name (without extension).
        :type sound_name: :class:`str`

        :param loops: Number of times to play through the sound.
        :type loops: :class:`int`

        :param key: The key to be used to identify the sound
        :type key: :class:`int`
        """
        channel = Mix_PlayChannel(-1, self.sounds[sound_name], loops)
        if channel == -1:
            LOG.error('Cannot play sound "{}"'.format(sound_name))
        elif key is not None:
            self.sound_map[key] = channel

    def stop_fx(self, key):
        """Stops a currently playing fx using the key to find teh proper channel.

        :param key: The key to be used to identify the sound
        :type key: :class:`int`
        """
        channel = self.sound_map.pop(key, None)
        if channel is not None:
            Mix_HaltChannel(channel)
