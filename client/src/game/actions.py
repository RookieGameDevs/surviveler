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
    if evt.state == MouseClickEvent.State.up and evt.context.player:
        LOG.debug('Action: {}'.format(evt))
        LOG.debug('Viewport pos: {},{}'.format(evt.x, evt.y))

        renderer_conf = evt.context.conf['Renderer']
        w = int(renderer_conf['width'])
        h = int(renderer_conf['height'])

        # transform viewport coordinates in terms of game units
        fov = evt.context.conf['Game'].getint('fov')
        x = (evt.x - w / 2.0) / fov
        y = (evt.y - h / 2.0) / fov
        LOG.debug('Normalized pos: {},{}'.format(x, y))

        # transform normalized coordinates to world coordinates by adding
        # the offset in game units to player's current position (no need to
        # transform using matrices, since player's position is the actual offset
        # from world origin)
        player = evt.context.player
        player_pos = Vec3(*player[Movable].position)
        pos = evt.context.scene.root.to_world(Vec3(x, y) + player_pos)
        LOG.debug('World pos: {},{},{}'.format(pos.x, pos.y, pos.z))

        msg = Message(MessageType.move, {
            MessageField.x_pos: float(pos.x),
            MessageField.y_pos: float(pos.y),
        })

        evt.context.msg_queue.append(msg)
