"""Implements audio system: music and sounds.

Files supported:
    * format: WAV, AIFF
    * bit depth: 16 bit
"""
from sdl2.ext.compat import byteify
from sdl2.sdlmixer import Mix_FadeOutMusic
from sdl2.sdlmixer import Mix_FadingMusic
from sdl2.sdlmixer import Mix_GetError
from sdl2.sdlmixer import Mix_HaltChannel
from sdl2.sdlmixer import Mix_HaltMusic
from sdl2.sdlmixer import Mix_LoadMUS
from sdl2.sdlmixer import Mix_LoadWAV
from sdl2.sdlmixer import Mix_PlayChannel
from sdl2.sdlmixer import Mix_PlayingMusic
from sdl2.sdlmixer import Mix_PlayMusic
from sdl2.sdlmixer import Mix_VolumeMusic
from random import choice as rand_choice
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

    Directory example:

        audio_root/
            fx/
                foo.aif
                bar.wav
                spam/
                    egg1.aif
                    egg2.aif
                    spam.aif
            music/
                mymusic.aif
    """

    def __init__(self, config):
        """Loads audio files.
        """

        self.volume = config.getint('Volume')

        # FIXME: audio file loading should happen using the resource manager
        # NOTE: right now these resources does not have the resource structure
        # and the mixer is feeded with every file into the directories: using
        # the resource manager will avoid problems and will permit to have a
        # more elastic way to interact with sounds.
        self.sounds = {}
        for filename in os.listdir(FX_ROOT):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(FX_ROOT, filename)
            event_sound_list = []
            if os.path.isdir(filepath):
                # We have more sounds for the same name
                for subfile in os.listdir(filepath):
                    subname, subext = os.path.splitext(subfile)
                    if subext not in ('.aif', '.wav'):
                        continue
                    subfilepath = os.path.join(filepath, subfile)
                    event_sound_list.append(subfilepath)
            else:
                if ext not in ('.aif', '.wav'):
                    continue
                # We have only 1 sound for this name
                event_sound_list = [filepath]

            self.sounds[name] = []
            for sound_filepath in event_sound_list:
                LOG.info('Loading sound {}'.format(sound_filepath))
                self.sounds[name].append((sound_filepath, Mix_LoadWAV(
                    byteify(sound_filepath, 'utf-8'))))

        self.musics = {}
        for filename in os.listdir(MUSIC_ROOT):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(MUSIC_ROOT, filename)
            LOG.info('Loading music {}'.format(filepath))
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
        if not volume:
            volume = self.volume
        Mix_VolumeMusic(volume)
        if Mix_PlayMusic(self.musics[music_name], loops) == -1:
            LOG.error('Cannot play music "{}"'.format(music_name))

    def music_is_fading(self):
        return Mix_FadingMusic()

    def music_is_playing(self):
        return Mix_PlayingMusic()

    def fade_out_music(self, ms):
        return Mix_FadeOutMusic(ms)

    def stop_music(self):
        return Mix_HaltMusic()

    def play_fx(self, sound_name, loops=0, key=None):
        """Plays a preloaded sound effect using the first available channel.

        :param: sound_name: The sound name (without extension).
        :type sound_name: :class:`str`

        :param loops: Number of times to play through the sound.
        :type loops: :class:`int`

        :param key: The key to be used to identify the sound
        :type key: :class:`int`
        """
        sounds = self.sounds[sound_name]
        filepath, sound = rand_choice(sounds)
        channel = Mix_PlayChannel(-1, sound, loops)
        if channel == -1:
            LOG.error('Cannot play sound "{}: {}"'.format(
                sound_name, filepath))
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
