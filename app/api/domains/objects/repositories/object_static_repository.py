from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.objects import ObjectStaticsTable


class ObjectStaticRepository(BaseRepository):
    def get_by_object_type_and_id(
        self, session: Session, object_type: str, object_id: int
    ) -> ObjectStaticsTable | None:
        stmt = (
            select(ObjectStaticsTable)
            .filter(ObjectStaticsTable.object_type == object_type)
            .filter(ObjectStaticsTable.object_id == object_id)
        )
        return self.fetch_first(session, stmt)

    def get_by_type_and_owner(
        self, session: Session, object_type: str | None = None, owner_uuid: UUID | None = None
    ) -> list[ObjectStaticsTable]:
        stmt = select(ObjectStaticsTable)

        if owner_uuid:
            type_filter = or_(
                ObjectStaticsTable.owner_1_id == owner_uuid,
                ObjectStaticsTable.owner_2_id == owner_uuid,
            )
            stmt = stmt.filter(type_filter)

        if object_type:
            stmt = stmt.filter(ObjectStaticsTable.object_type == object_type)

        return self.fetch_all(session, stmt)

    def get_by_source(self, session: Session, source_key: str) -> ObjectStaticsTable | None:
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.source_identifier == source_key)
        return self.fetch_first(session, stmt)

    def does_codes_exists(self, session: Session, codes: set[str]) -> tuple[bool, set[str]]:
        if not len(codes):
            return True, set()

        stmt = select(ObjectStaticsTable.code).where(ObjectStaticsTable.code.in_(codes))
        existing: set[str] = set(session.execute(stmt).scalars())
        missing: set[str] = set(codes) - existing

        return len(missing) == 0, missing
