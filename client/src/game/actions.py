from core.events import MouseClickEvent
from events import subscriber
from game.components import Movable
from matlib import Vec3
from network import Message
from network import MessageField
from network import MessageType
import logging

LOG = logging.getLogger(__name__)


@subscriber(MouseClickEvent)
def handle_mouse_click(evt):
    if evt.state == MouseClickEvent.State.up and evt.client.player:
        LOG.debug('Action: {}'.format(evt))
        LOG.debug('Viewport pos: {},{}'.format(evt.x, evt.y))

        # transform viewport coordinates in terms of game units
        fov = evt.client.config.getint('fov')
        x = (evt.x - evt.client.renderer.width / 2.0) / fov
        y = (evt.y - evt.client.renderer.height / 2.0) / fov
        LOG.debug('Normalized pos: {},{}'.format(x, y))

        # transform normalized coordinates to world coordinates by adding
        # the offset in game units to player's current position (no need to
        # transform using matrices, since player's position is the actual offset
        # from world origin)
        player = evt.client.player
        player_pos = Vec3(*player[Movable].position)
        pos = evt.client.scene.root.to_world(Vec3(x, y) + player_pos)
        LOG.debug('World pos: {},{},{}'.format(pos.x, pos.y, pos.z))

        msg = Message(MessageType.move, {
            MessageField.x_pos: float(pos.x),
            MessageField.y_pos: float(pos.y),
        })

        evt.client.proxy.enqueue(msg)
