from core.events import MouseClickEvent
from events import subscriber
from matlib import Vec3
from network import Message
from network import MessageField
from network import MessageType
import logging

LOG = logging.getLogger(__name__)


@subscriber(MouseClickEvent)
def handle_mouse_click(evt):
    if evt.state == MouseClickEvent.State.up:
        LOG.info('Action: {}'.format(evt))
        LOG.info('Viewport pos: {},{}'.format(evt.x, evt.y))

        # transform viewport coordinates in terms of game units
        fov = evt.client.config.getint('fov')
        x = (evt.x - evt.client.renderer.width / 2.0) / fov
        y = (evt.y - evt.client.renderer.height / 2.0) / fov
        LOG.info('Normalized pos: {},{}'.format(x, y))

        # transform normalized coordinates to world coordinates
        pos = evt.client.scene.root.to_world(Vec3(x, y, 0))
        LOG.info('World pos: {},{},{}'.format(pos.x, pos.y, pos.z))

        msg = Message(MessageType.move, {
            MessageField.x_pos: int(round(pos.x)),
            MessageField.y_pos: int(round(pos.y)),
        })

        evt.client.proxy.enqueue(msg)
