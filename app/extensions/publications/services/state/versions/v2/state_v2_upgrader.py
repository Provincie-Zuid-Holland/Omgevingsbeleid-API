from abc import ABCMeta

from app.extensions.publications.services.state.state import State
from app.extensions.publications.services.state.state_upgrader import StateUpgrader
from ..v1.state_v1 import StateV1


class StateV2Upgrader(StateUpgrader):
    def __init__(self):
        pass

    def upgrade(self, state: State) -> State:
        if state.get_schema_version() != StateV1.get_schema_version():
            raise RuntimeError("Unexpected state provided")


