from typing import Optional, Type

from app.extensions.publications.services.state.state import State, StateSchema
from app.extensions.publications.services.state.state_version_factory import StateVersionFactory
from app.extensions.publications.tables.tables import (
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
    PublicationVersionTable,
)


class StateLoader:
    def __init__(self, state_version_factory: StateVersionFactory):
        self._state_version_factory: StateVersionFactory = state_version_factory

    def load(self, state_dict: dict) -> State:
        schema: StateSchema = StateSchema.parse_obj(state_dict)
        version_model: Type[State] = self._state_version_factory.get_state_model(
            schema.Schema_Version,
        )
        state: State = version_model.parse_obj(state_dict["Data"])
        return state

    def load_from_publication_version(self, publication_version: PublicationVersionTable) -> Optional[State]:
        environment: PublicationEnvironmentTable = publication_version.Environment
        if not environment.Has_State:
            return None

        if environment.Active_State is None:
            raise RuntimeError("Unexpecting to not have an active state while the environment is stateful")
        current_state_table: PublicationEnvironmentStateTable = environment.Active_State
        current_state_dict: dict = current_state_table.State

        state: State = self.load(current_state_dict)
        return state
