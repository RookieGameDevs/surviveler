from abc import ABC
from abc import abstractmethod
import logging


LOG = logging.getLogger(__name__)


class Component(ABC):
    """Base class for all components"""

    @abstractmethod
    def __init__(self):
        pass
