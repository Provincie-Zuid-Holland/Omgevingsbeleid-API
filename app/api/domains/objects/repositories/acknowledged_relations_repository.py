from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable


class AcknowledgedRelationsRepository:
    def get_by_codes(self, session: Session, code_a: str, code_b: str) -> AcknowledgedRelationsTable | None:
        from_code, to_code = sorted([code_a, code_b])
        stmt = select(AcknowledgedRelationsTable).filter(
            and_(
                AcknowledgedRelationsTable.from_code == from_code,
                AcknowledgedRelationsTable.to_code == to_code,
                AcknowledgedRelationsTable.deleted_at.is_(None),
                AcknowledgedRelationsTable.denied.is_(None),
            )
        )
        return session.scalars(stmt).first()

    def get_with_filters(
        self,
        session: Session,
        code: str,
        requested_by_me: bool,
        acknowledged: bool | None,
        show_inactive: bool = True,
    ) -> list[AcknowledgedRelationsTable]:
        filters = []

        if requested_by_me:
            filters.append(AcknowledgedRelationsTable.requested_by_code == code)
        else:
            filters.append(
                or_(
                    AcknowledgedRelationsTable.from_code == code,
                    AcknowledgedRelationsTable.to_code == code,
                )
            )

        if acknowledged is not None:
            if acknowledged is True:
                filters.append(AcknowledgedRelationsTable.is_acknowledged)
            else:
                filters.append(
                    or_(
                        AcknowledgedRelationsTable.from_acknowledged.is_(None),
                        AcknowledgedRelationsTable.to_acknowledged.is_(None),
                    )
                )

        if show_inactive is False:
            filters.append(
                and_(
                    AcknowledgedRelationsTable.deleted_at.is_(None),
                    AcknowledgedRelationsTable.denied.is_(None),
                )
            )

        stmt = select(AcknowledgedRelationsTable).filter(*filters)
        rows: list[AcknowledgedRelationsTable] = list(session.scalars(stmt).all())
        return rows
