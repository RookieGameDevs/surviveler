from enum import IntEnum
from enum import unique
from events import subscriber
from game import Entity
from game.events import BuildingDisappear
from game.events import BuildingSpawn
import logging


LOG = logging.getLogger(__name__)


@unique
class BuildingType(IntEnum):
    """Enumeration of the possible buildings"""
    barricade = 0


class Building(Entity):
    """Game entity which represents a building."""


@subscriber(BuildingSpawn)
def building_spawn(evt):
    """Create a building.

    A building of the appropriate type is created and placed into the game.
    """
    # TODO: Create the building object
    # TODO: Place the building in the appropriate position
    # TODO: Change the walkable matrix appropriately


@subscriber(BuildingDisappear)
def building_disappear(evt):
    """Remove a building from the game.
    """
    # TODO: Remove the building object
    # TODO: Change the walkable matrix appropriately
