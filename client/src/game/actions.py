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


def cast_ray(mouse_coords, view_w, view_h, camera):
    """Cast a ray from mouse to world."""
    x, y = mouse_coords

    # transform viewport coordinates to NDC space
    x_ndc = 2.0 * x / view_w - 1.0
    y_ndc = 1.0 - 2 * y / view_h
    z_ndc = -1.0

    # make a homogeneous clip coordinates 4D vector and compute eye coordinates
    # vector
    m_projection = Mat(camera.projection)
    m_projection.invert()
    v_clip = Vec(x_ndc, y_ndc, z_ndc, 1.0)
    v_eye = m_projection * v_clip

    # change the vector so that only X and Y components are used and Z just
    # points forward, W is of no use
    v_eye.z = -1.0
    v_eye.w = 0.0

    # transform eye coordinates to world coordinates
    m_modelview = Mat(camera.modelview)
    m_modelview.invert()
    v_world = m_modelview * v_eye
    v_world.norm()

    return v_world


@subscriber(MouseClickEvent)
def handle_mouse_click(evt):
    if evt.state == MouseClickEvent.State.up and evt.context.player:
        LOG.debug('Action: {}'.format(evt))
        LOG.debug('Viewport pos: {},{}'.format(evt.x, evt.y))

        renderer_conf = evt.context.conf['Renderer']
        w = int(renderer_conf['width'])
        h = int(renderer_conf['height'])

        ray = cast_ray((evt.x, evt.y), w, h, evt.context.camera)
        LOG.debug('Ray: {}'.format(ray))

        # TODO: replace this with ray-plane intersection result

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
        player_pos = Vec(*player[Movable].position)
        pos = evt.context.scene.root.to_world(Vec(x, y) + player_pos)
        LOG.debug('World pos: {},{},{}'.format(pos.x, pos.y, pos.z))

        msg = Message(MessageType.move, {
            MessageField.x_pos: float(pos.x),
            MessageField.y_pos: float(pos.y),
        })

        evt.context.msg_queue.append(msg)
