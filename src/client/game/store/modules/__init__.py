"""Store modules: all the modules are included here and combined properly"""

from .ui import reducer as ui_reducer
from revived.reducer import combine_reducers
from revived.reducer import reducer
from revived.store import ActionType as StoreActionType


@reducer(StoreActionType.INIT)
def init(prev, action):
    return {}


reducer = combine_reducers(init, ui=ui_reducer)
