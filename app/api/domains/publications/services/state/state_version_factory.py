import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.state.state import State, StateSchema
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader
from app.api.domains.publications.services.state.versions import ActiveState


class StateVersionFactory:
    def __init__(self, versions: list[type[State]], upgraders: list[StateUpgrader]):
        self._versions: dict[int, type[State]] = {v.get_schema_version(): v for v in versions}
        self._upgraders: dict[int, StateUpgrader] = {u.get_input_schema_version(): u for u in upgraders}

    async def get_state_model(self, session: AsyncSession, environment_id: uuid.UUID, state_dict: dict) -> ActiveState:
        schema: StateSchema = StateSchema.model_validate(state_dict)
        if schema.Schema_Version not in self._versions:
            raise RuntimeError(f"State schema version '{schema.Schema_Version}' is not registered")

        version_model: type[State] = self._versions[schema.Schema_Version]
        state: State = version_model.model_validate(state_dict["Data"])
        state = await self._upgrade(session, environment_id, state)

        return state

    async def _upgrade(self, session: AsyncSession, environment_id: uuid.UUID, state: State) -> ActiveState:
        guard_counter: int = len(self._upgraders)

        while not isinstance(state, ActiveState):
            upgrader: StateUpgrader | None = self._upgraders.get(state.get_schema_version())
            if upgrader is None:
                raise RuntimeError(f"No upgrader created for old state with version {state.get_schema_version()}")

            state = await upgrader.upgrade(
                session=session,
                environment_uuid=environment_id,
                old_state=state,
            )

            if guard_counter < 0:
                raise RuntimeError(
                    f"Upgrading the state is hanging and ending with version '{state.get_schema_version()}'"
                )
            guard_counter -= 1

        return state
