from core.events import MouseClickEvent
from events import subscriber
from network import Message
from network import MessageField
from network import MessageType
import logging

LOG = logging.getLogger(__name__)


@subscriber(MouseClickEvent)
def handle_mouse_click(evt):
    # TODO: convert screen coordinates in world coordinates

    # FIXME: remove hardcoded values when the conversion is ready
    x, y = 1.0, 1.0
    msg = Message(
        MessageType.move, {
            MessageField.x_pos: x,
            MessageField.y_pos: y,
        })

    # FIXME: uncomment the message enqueueing when the server is able to receive
    # move messages
    # evt.client.proxy.enqueue(msg)
    LOG.info('Action: {}'.format(evt))
