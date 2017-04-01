from core.events import KeyPressEvent
from core.events import MouseClickEvent
from core.events import MouseMoveEvent
from events import send_event
from events import subscriber
from game.events import EntityPick
from game.events import GameModeToggle
from matlib.vec import Vec
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


def start_move_action(context, position):
    """Start a move action to the defined position.

    :param context: The game context.
    :type context: :class:`context.Context`

    :param position: The position in world ccoordinates
    :type position: :class:`tuple`
    """
    msg = Message(MessageType.move, {
        MessageField.x_pos: position[0],
        MessageField.y_pos: position[1],
    })

    context.msg_queue.append(msg)


def start_build_action(context, position):
    """Start a build action to the defined position.

    NOTE: the game context has all the information required.

    :param context: The game context.
    :type context: :class:`context.Context`

    :param position: The position in world ccoordinates
    :type position: :class:`tuple`
    """
    building_type = context.building_type
    msg = Message(MessageType.build, {
        MessageField.building_type: building_type,
        MessageField.x_pos: position[0],
        MessageField.y_pos: position[1],
    })

    context.msg_queue.append(msg)
    send_event(GameModeToggle(context.GameMode.building))


def entity_picked(context, entity):
    """An entity was picked with the mouse click.

    :param context: The game context.
    :type context: :class:`context.Context`

    :param entity: The entity picked
    :type entity: :class:`game.entities.entity.Entity`
    """
    send_event(EntityPick(entity))


@subscriber(MouseClickEvent)
def handle_mouse_click(evt):
    context = evt.context
    if evt.state == MouseClickEvent.State.up and context.player:

        LOG.debug('Action: {}'.format(evt))
        LOG.debug('Viewport pos: {},{}'.format(evt.x, evt.y))

        renderer_conf = context.conf['Renderer']
        w = int(renderer_conf['width'])
        h = int(renderer_conf['height'])

        x, y = evt.x, evt.y
        camera = context.camera

        target = ray_cast(x, y, w, h, camera)
        world_pos = to_world(target.x, target.y, target.z)
        LOG.debug('World pos: {}'.format(world_pos))
        pos = world_pos.x, world_pos.y

        if context.game_mode == context.GameMode.default:
            c_pos, ray = camera.trace_ray(x, y, w, h)
            entity = context.pick_entity(c_pos, ray)
            if entity:
                # step 1 - try to pick entities
                entity_picked(context, entity)
            else:
                # step 2 - just find the destination and start a movement
                start_move_action(context, pos)
        elif context.game_mode == context.GameMode.building:
            start_build_action(context, pos)


def place_building_template(context, x, y):
    """Places the template building on the world.

    :param context: The game context.
    :type context: :class:`context.Context`

    :param x: The non-clamped x-axis coordinate.
    :type x: int

    :param y: The non-clamped y-ayis coordinate.
    :type y: int
    """
    map_res = context.res_mgr.get('/map')

    renderer_conf = context.conf['Renderer']
    w = int(renderer_conf['width'])
    h = int(renderer_conf['height'])
    camera = context.camera

    target = ray_cast(x, y, w, h, camera)
    world_pos = to_world(target.x, target.y, target.z)
    pos = clamp_to_grid(
            world_pos.x, world_pos.y, map_res.data['scale_factor'])
    context.building_template.pos = pos


@subscriber(MouseMoveEvent)
def handle_mouse_move(evt):
    """Handles the mouse move event.

    Places the building template on the world under the mouse cursor.

    :prarm evt: The mouse move event.
    :type evt: :class:`core.events.MouseMoveEvent`
    """
    context = evt.context
    if context.game_mode == context.GameMode.building:
        place_building_template(context, evt.x, evt.y)


@subscriber(KeyPressEvent)
def handle_key_press(evt):
    """Handles the B key pressed event.

    Toggles the building game mode.

    :param evt: The key press event.
    :type evt: :class:`core.events.KeyPressEvent`
    """
    context = evt.context
    if evt.key == sdl.SDLK_b:
        send_event(GameModeToggle(context.GameMode.building))
