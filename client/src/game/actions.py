from core.events import KeyPressEvent
from core.events import MouseClickEvent
from core.events import MouseMoveEvent
from events import send_event
from events import subscriber
from game.components import Movable
from game.events import GameModeToggle
from matlib import Vec
from network import Message
from network import MessageField
from network import MessageType
from utils import clamp_to_grid
from utils import to_world
import logging
import sdl2 as sdl

LOG = logging.getLogger(__name__)


def ray_cast(x, y, w, h, camera):
    """Returns the world coordinates related to the given x,y coordinates.

    :param x: The x coordinate relative to screen
    :type x: int

    :param y: The y coordinate relative to screen
    :type y: int

    :param w: The width of the screen
    :type w: int

    :param h: The height of the screen
    :type h: int

    :param camera: The camera we are using to trace the ray.
    :type camera: :class:`renderer.Camera`

    :returns: The point in world coordinates.
    :type: :class:`mat.Vec`
    """
    # Find the direction applying the modelview matrix to the facing direction
    # of the camera
    pos, ray = camera.trace_ray(x, y, w, h)

    # The normal vector for the y=0 plane
    norm = Vec(0, 1, 0)

    # And here finally we have the target of the click in world coordinates More
    # reference about the used math here:
    #  * http://antongerdelan.net/opengl/raycasting.html
    t = - (pos.dot(norm)) / ray.dot(norm)
    return pos + (ray * t)


@subscriber(MouseClickEvent)
def handle_mouse_click(evt):
    if evt.state == MouseClickEvent.State.up and evt.context.player:
        LOG.debug('Action: {}'.format(evt))
        LOG.debug('Viewport pos: {},{}'.format(evt.x, evt.y))

        renderer_conf = evt.context.conf['Renderer']
        w = int(renderer_conf['width'])
        h = int(renderer_conf['height'])

        camera = evt.context.camera
        target = ray_cast(evt.x, evt.y, w, h, camera)
        world_pos = to_world(target.x, target.y, target.z)
        LOG.debug('World pos: {}'.format(world_pos))

        msg = Message(MessageType.move, {
            MessageField.x_pos: world_pos.x,
            MessageField.y_pos: world_pos.y,
        })

        evt.context.msg_queue.append(msg)


@subscriber(MouseMoveEvent)
def handle_mouse_move(evt):
    context = evt.context
    if context.game_mode == context.GameMode.building:
        map_res = context.res_mgr.get('/map')

        renderer_conf = context.conf['Renderer']
        w = int(renderer_conf['width'])
        h = int(renderer_conf['height'])
        camera = context.camera

        target = ray_cast(evt.x, evt.y, w, h, camera)
        world_pos = to_world(target.x, target.y, target.z)
        pos = clamp_to_grid(
                world_pos.x, world_pos.y, map_res.data['scale_factor'])
        context.building_template[Movable].position = pos


@subscriber(KeyPressEvent)
def handle_key_press(evt):
    """Handle the B key pressed event.

    Toggles the building game mode.

    :param evt: The key press event.
    :type evt: :class:`core.events.KeyPressEvent`
    """
    context = evt.context
    if evt.key == sdl.SDLK_b:
        send_event(GameModeToggle(context.GameMode.building))
