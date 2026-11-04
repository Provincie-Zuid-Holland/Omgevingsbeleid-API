from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.repository.publication_environment_repository import (
    PublicationEnvironmentRepository,
)
from app.api.domains.publications.services.state.state_version_factory import StateVersionFactory
from app.api.domains.publications.services.state.versions import ActiveState
from app.core.tables.publications import (
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
    PublicationVersionTable,
)


class StateLoader:
    def __init__(
        self,
        state_version_factory: StateVersionFactory,
        environment_repository: PublicationEnvironmentRepository,
    ):
        self._state_version_factory: StateVersionFactory = state_version_factory
        self._environment_repository: PublicationEnvironmentRepository = environment_repository

    async def load_from_publication_version(
        self, session: AsyncSession, publication_version: PublicationVersionTable
    ) -> ActiveState | None:
        environment: PublicationEnvironmentTable = publication_version.publication.environment
        return await self.load_from_environment(session, environment)

    async def load_from_environment(
        self, session: AsyncSession, environment: PublicationEnvironmentTable
    ) -> ActiveState | None:
        if not environment.has_state:
            return None

        current_state_table: PublicationEnvironmentStateTable | None = None
        if environment.active_state_id is not None:
            current_state_table = await self._environment_repository.get_state_by_id(
                session, environment.active_state_id
            )
        if current_state_table is None:
            raise RuntimeError("Unexpecting to not have an active state while the environment is stateful")
        current_state_dict: dict = current_state_table.state

        state: ActiveState = await self._state_version_factory.get_state_model(
            session,
            environment.id,
            current_state_dict,
        )

        return state
