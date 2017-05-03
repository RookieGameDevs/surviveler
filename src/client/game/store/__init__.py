"""Module defining the store and the related utility functions"""

from .modules import reducer as root_reducer
from revived.store import Store

# FIXME: try to find a way to not export the whole store
STORE = Store(root_reducer)
