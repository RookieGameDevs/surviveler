from events import subscriber
from game.events import TimeUpdate
import logging


LOG = logging.getLogger(__name__)
DAY_START = 5
NIGHT_START = 17
MUSIC_FADE_OUT_TIME = 25000

daytime_music = {'day': 'day', 'night': 'sunset'}


def get_daytime(hour):
    if DAY_START <= hour < NIGHT_START:
        return 'day'
    return 'night'


@subscriber(TimeUpdate)
def deejay(evt):
    """Change music based on daytime.
    """
    hour, minute = evt.hour, evt.minute
    audio_mgr = evt.context.audio_mgr
    if (hour, minute) in ((DAY_START, 0), (NIGHT_START, 0)):
        if audio_mgr.music_is_playing():
            LOG.info('Music fade out...')
            audio_mgr.fade_out_music(MUSIC_FADE_OUT_TIME)

    if not audio_mgr.music_is_playing():
        daytime = get_daytime(hour)
        music = daytime_music[daytime]
        audio_mgr.play_music(music)
        LOG.info('Starting music for {daytime}: {music}'.format(
            daytime=daytime, music=music)
        )
