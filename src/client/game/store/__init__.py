"""Module defining the store and the related utility functions"""

from .modules import reducer as root_reducer
from abc import ABC
from abc import abstractmethod
from revived.store import Store

# Create the store instance
STORE = Store(root_reducer)


def ConnectedBaseClass(map_state_to_props):
    """Generetor of ABC classes to be inherited by state-aware object.
    """
    class _class(ABC):
        _map_state_to_props = map_state_to_props

        def __init__(self):
            STORE.subscribe(lambda: self.state_changed())

        def dispatch(self, action):
            """Simply forwards to the store the action to be dispatched.
            """
            STORE.dispatch(action)

        def state_changed(self):
            """Checks the stored properties with the new ones.

            In case of differences: calls the on_state_change method implemented
            in the subclass.
            """
            props = getattr(self, 'props', None)
            new_props = _class._map_state_to_props(STORE.get_state())
            if props != new_props:
                self.on_state_change(new_props)
                self.props = new_props

        @abstractmethod
        def on_state_change(self, new_props):
            """This method should be implemented in state-aware objects.

            This method will be called everytime the relevant properties for the
            object change.
            """
            pass

    return _class


def connect(map_state_to_props=None):
    """Decorates state-aware classes.
    """
    def wrapper(cls):
        base = ConnectedBaseClass(map_state_to_props or (lambda x: {}))

        class _class(cls, base):
            __module__ = cls.__module__
            __name__ = cls.__name__
            __qualname__ = cls.__qualname__
            __doc__ = cls.__doc__

            def __init__(self, *args, **kwargs):
                cls.__init__(self, *args, **kwargs)
                base.__init__(self)

        return _class

    return wrapper


def dispatch(action):
    """Dispatches an action to the store.
    """
    STORE.dispatch(action)
