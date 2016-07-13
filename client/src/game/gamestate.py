from enum import IntEnum
from enum import unique
from events import send_event
from game.entities.actor import ActorType
from game.entities.building import BuildingType
from game.events import ActorDisappear
from game.events import ActorIdle
from game.events import ActorMove
from game.events import ActorSpawn
from game.events import ActorStatusChange
from game.events import BuildingDisappear
from game.events import BuildingSpawn
from game.events import BuildingStatusChange
from game.events import CharacterBuildingStart
from game.events import CharacterBuildingStop
from game.events import TimeUpdate
from network import MessageField as MF
import logging


LOG = logging.getLogger(__name__)


class GameStateManager:
    """Game state manager.

    Instances of this objects are meant to handle a configurable ring buffer of
    game states.
    """
    def __init__(self, size):
        """Constructur.

        :param size: the size of the ring buffer
        :type size: int
        """
        self.size = size
        # NOTE: -1 means that the buffer is empty. This should only happen
        # during initialization
        self.cur = -1
        self.gamestate_buf = [None for x in range(size)]

    def push(self, gamestate):
        """Push a new gamestate into the ring bffer.

        :param gamestate: The gamestate to be pushed.
        :type gamestate: dict
        """
        self.cur = (self.cur + 1) % self.size
        self.gamestate_buf[self.cur] = gamestate

    def get(self, n=1):
        """Get n gamestates from the ring buffer.

        :param n: The number of gamestates to be returned
        :type n: int

        :returns: The list of gamestates
        :rtype: list
        """
        if n > self.size:
            raise IndexError('exceeded number of gamestates')

        return [
            self.gamestate_buf[i]
            for i in range(self.cur, self.cur - n, -1)
        ]


__MANAGER = GameStateManager(2)
__PROCESSORS = []


def processor(f):
    """Decorator for gamestate processors.
    """
    __PROCESSORS.append(f)
    return f


def process_gamestate(gamestate):
    """Director of all the gamestate handlers.

    Pushes the gamestate in the global gamestate manager and calls every
    processor passing the gamestate manager as parameter.

    :param gamestate: The current gamestate
    :type gamestate: dict
    """
    __MANAGER.push(gamestate)
    for proc in __PROCESSORS:
        proc(__MANAGER)


def gamestate_entities(gs_mgr):
    """Returns the entities available in the gamestate.

    :param gs_mgr: the gamestate manager.
    :type gs_mgr: :class:`game.gamestate.GameStateManager`

    :returns: server id, entity
    :rtype: tuple
    """
    gamestate = gs_mgr.get()[0]
    for srv_id, e in gamestate.get(MF.entities, {}).items():
        yield srv_id, e


@unique
class ActionType(IntEnum):
    """Enum of the various possible ActionType"""
    idle = 0
    move = 1
    build = 2
    repair = 3
    attack = 4


@processor
def handle_actor_spawn(gs_mgr):
    """Check for new entities and send the appropriate events.

    Check if there are new entities that were not in the previous gamestate.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: dict
    """
    n, o = gs_mgr.get(2)
    o = o or {}
    new, old = n[MF.entities], o.get(MF.entities, {})
    new_entities = set(new) - set(old)
    for ent in new_entities:
        data = new[ent]
        actor_type = ActorType(data[MF.entity_type])
        cur_hp = data[MF.cur_hp]
        evt = ActorSpawn(ent, actor_type, cur_hp)
        send_event(evt)


@processor
def handle_actor_disappear(gs_mgr):
    """Check for disappeared entities and send the appropriate events.

    Check if there are new entities that were not in the previous gamestate.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: dict
    """
    n, o = gs_mgr.get(2)
    o = o or {}
    new, old = n[MF.entities], o.get(MF.entities, {})
    old_entities = set(old) - set(new)
    for ent in old_entities:
        evt = ActorDisappear(ent)
        send_event(evt)


@processor
def handle_actor_idle(gs_mgr):
    """Handles entities in idle state and fires ActorIdle event for them.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: dict
    """
    for srv_id, entity in gamestate_entities(gs_mgr):
        # Update the position of every idle entity
        if entity.get(MF.action_type, ActionType.idle) == ActionType.idle:
            x, y = entity[MF.x_pos], entity[MF.y_pos]
            evt = ActorIdle(srv_id, x, y)
            send_event(evt)


@processor
def handle_actor_move(gs_mgr):
    """Handles moving entities and fires ActorMove event for them.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: dict
    """
    for srv_id, entity in gamestate_entities(gs_mgr):
        if entity.get(MF.action_type, None) == ActionType.move:
            action = entity[MF.action]
            position = entity[MF.x_pos], entity[MF.y_pos]
            path = action[MF.path]

            send_event(ActorMove(
                srv_id,
                position=position,
                path=path,
                speed=action[MF.speed]))


@processor
def handle_character_start_building(gs_mgr):
    """Handles building entities and fires CharacterBuildingStart event for them.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: dict
    """
    n, o = gs_mgr.get(2)
    o = o or {}
    new, old = n[MF.entities], o.get(MF.entities, {})
    for e_id, entity in new.items():
        if entity[MF.action_type] in {ActionType.build, ActionType.repair}:
            if e_id not in old or old[e_id][MF.action_type] not in {ActionType.build, ActionType.repair}:
                send_event(CharacterBuildingStart(e_id))


@processor
def handle_character_stop_building(gs_mgr):
    """Handles entities that stopped building and fires CharacterBuildingStop
    event for them.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: dict
    """
    n, o = gs_mgr.get(2)
    o = o or {}
    new, old = n[MF.entities], o.get(MF.entities, {})
    for e_id, entity in old.items():
        if entity[MF.action_type] in {ActionType.build, ActionType.repair}:
            if e_id not in new or new[e_id][MF.action_type] not in {ActionType.build, ActionType.repair}:
                send_event(CharacterBuildingStop(e_id))


@processor
def handle_actor_health(gs_mgr):
    """Check for entity health changes and send the appropriate event.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: :class:`dict`
    """
    n, o = gs_mgr.get(2)
    o = o or {}
    new, old = n[MF.entities], o.get(MF.entities, {})
    for e_id, entities in new.items():
        if e_id in old:
            new_hp = entities[MF.cur_hp]
            old_hp = old[e_id][MF.cur_hp]
            hp_changed = new_hp != old_hp
            if hp_changed:
                send_event(ActorStatusChange(e_id, old_hp, new_hp))


@processor
def handle_time(gs_mgr):
    """Handles time change and sends time update event.

    :param gs_mgr: The gamestate manager.
    :type gs_mgr: :class:`game.gamestate.GameStateManager`
    """
    total_minutes = gs_mgr.get()[0].get(MF.time, 0)
    h, m = int(total_minutes / 60), total_minutes % 60
    send_event(TimeUpdate(h, m))


def handle_buildings(selected, buildings, event):
    """Generic function for building spawning/disappearing handling.

    :param selected: The ids of the building to be handled.
    :type selected: :class:`set`

    :param buildings: The mapping of all the buildings in the gamestate.
    :type buildings: :class:`dict`

    :param event: The event class to be used
    :type event: :class:`type`
    """
    for building in selected:
        data = buildings[building]
        b_type = BuildingType(data[MF.building_type])
        pos = data[MF.x_pos], data[MF.y_pos]
        cur_hp = data[MF.cur_hp]
        completed = data[MF.completed]
        evt = event(building, b_type, pos, cur_hp, completed)
        send_event(evt)


@processor
def handle_building_spawn(gs_mgr):
    """Check for new buildings and send the appropriate events.

    Check if there are new buildings that were not in the previous gamestate.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: dict
    """
    n, o = gs_mgr.get(2)
    o = o or {}
    new, old = n[MF.buildings], o.get(MF.buildings, {})
    new_buildings = set(new) - set(old)
    handle_buildings(new_buildings, new, BuildingSpawn)


@processor
def handle_building_disappear(gs_mgr):
    """Check for disappeared buildings and send the appropriate events.

    Check if there are new buildings that were not in the previous gamestate.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: dict
    """
    n, o = gs_mgr.get(2)
    o = o or {}
    new, old = n[MF.buildings], o.get(MF.buildings, {})
    old_buildings = set(old) - set(new)
    handle_buildings(old_buildings, old, BuildingDisappear)


@processor
def handle_building_health(gs_mgr):
    """Check for building health/satatus changes and send the appropriate event.

    :param gs_mgr: the gs_mgr
    :type gs_mgr: :class:`dict`
    """
    n, o = gs_mgr.get(2)
    o = o or {}
    new, old = n[MF.buildings], o.get(MF.buildings, {})
    for b_id, building in new.items():
        if b_id in old:
            new_hp = building[MF.cur_hp]
            old_hp = old[b_id][MF.cur_hp]
            hp_changed = new_hp != old_hp
            status_changed = building[MF.completed] == old[b_id][MF.completed]
            if hp_changed or status_changed:
                send_event(BuildingStatusChange(
                    b_id, old_hp, new_hp, building[MF.completed]))
