import uuid
from typing import Dict, List, Optional, Type

from sqlalchemy.orm import Session

from app.api.domains.publications.services.state.state import State, StateSchema
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader
from app.api.domains.publications.services.state.versions import ActiveState


class StateVersionFactory:
    def __init__(self, versions: List[Type[State]], upgraders: List[StateUpgrader]):
        self._versions: Dict[int, Type[State]] = {v.get_schema_version(): v for v in versions}
        self._upgraders: Dict[int, StateUpgrader] = {u.get_input_schema_version(): u for u in upgraders}

    def get_state_model(self, session: Session, environment_uuid: uuid.UUID, state_dict: dict) -> ActiveState:
        schema: StateSchema = StateSchema.model_validate(state_dict)
        if schema.Schema_Version not in self._versions:
            raise RuntimeError(f"State schema version '{schema.Schema_Version}' is not registered")

        version_model: Type[State] = self._versions[schema.Schema_Version]
        state: State = version_model.model_validate(state_dict["Data"])
        state = self._upgrade(session, environment_uuid, state)

        return state

    def _upgrade(self, session: Session, environment_uuid: uuid.UUID, state: State) -> ActiveState:
        guard_counter: int = len(self._upgraders)

        while not isinstance(state, ActiveState):
            upgrader: Optional[StateUpgrader] = self._upgraders.get(state.get_schema_version())
            if upgrader is None:
                raise RuntimeError(f"No upgrader created for old state with version {state.get_schema_version()}")

            state = upgrader.upgrade(
                session=session,
                environment_uuid=environment_uuid,
                old_state=state,
            )

            if guard_counter < 0:
                raise RuntimeError(
                    f"Upgrading the state is hanging and ending with version '{state.get_schema_version()}'"
                )
            guard_counter -= 1

        return state
