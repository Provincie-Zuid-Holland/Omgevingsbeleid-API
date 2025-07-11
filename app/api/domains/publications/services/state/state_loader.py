from typing import Optional

from sqlalchemy.orm import Session

from app.api.domains.publications.services.state.state_version_factory import StateVersionFactory
from app.api.domains.publications.services.state.versions import ActiveState
from app.core.tables.publications import (
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
    PublicationVersionTable,
)


class StateLoader:
    def __init__(self, state_version_factory: StateVersionFactory):
        self._state_version_factory: StateVersionFactory = state_version_factory

    def load_from_publication_version(
        self, session: Session, publication_version: PublicationVersionTable
    ) -> Optional[ActiveState]:
        environment: PublicationEnvironmentTable = publication_version.Publication.Environment
        return self.load_from_environment(session, environment)

    def load_from_environment(self, session, environment: PublicationEnvironmentTable) -> Optional[ActiveState]:
        if not environment.Has_State:
            return None

        if environment.Active_State is None:
            raise RuntimeError("Unexpecting to not have an active state while the environment is stateful")
        current_state_table: PublicationEnvironmentStateTable = environment.Active_State
        current_state_dict: dict = current_state_table.State

        state: ActiveState = self._state_version_factory.get_state_model(
            session,
            environment.UUID,
            current_state_dict,
        )

        return state
