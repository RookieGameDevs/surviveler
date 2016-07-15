from events import subscriber
from game.events import DaytimeChange
from game.events import IncomingDaytimeChange
import logging


LOG = logging.getLogger(__name__)

daytime_music = {'day': 'day', 'night': 'sunset'}


@subscriber(IncomingDaytimeChange)
def fade_out_music(evt):
    LOG.info('Incoming daytime change: {curr} -> {next}'.format(
        curr=evt.current_daytime, next=evt.next_daytime))
    # if evt.context.audio_mgr.music_is_playing():
    evt.context.audio_mgr.fade_out_music(20000)


@subscriber(DaytimeChange)
def start_music(evt):
    music = daytime_music[evt.daytime]
    LOG.info('Starting music for {daytime}: {music}'.format(
        daytime=evt.daytime, music=music)
    )
    assert not evt.context.audio_mgr.music_is_playing()
    evt.context.audio_mgr.play_music(music)
