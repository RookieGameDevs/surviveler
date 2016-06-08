from core.events import MouseClickEvent
from events import subscriber
from game.components import Movable
from matlib import Mat
from matlib import Vec
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

        # Position on near clipping plane
        pos = evt.context.camera.unproject(evt.x, evt.y, w, h)
        camera = evt.context.camera
        d = camera.modelview * Vec(0, 0, -1)
        norm = Vec(0, 0, -1)
        d.norm()

        t = - (pos.dot(norm)) / d.dot(norm)
        target = pos + (d * t)
        LOG.debug('World pos: {},{},{}'.format(target.x, target.y, target.z))

        msg = Message(MessageType.move, {
            MessageField.x_pos: float(target.x),
            MessageField.y_pos: float(target.y),
        })

        evt.context.msg_queue.append(msg)
