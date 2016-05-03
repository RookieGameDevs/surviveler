from core.events import MouseClickEvent
from events import subscriber
import logging

LOG = logging.getLogger(__name__)


@subscriber(MouseClickEvent)
def handle_mouse_click(evt):
    LOG.info('Action: {}'.format(evt))
