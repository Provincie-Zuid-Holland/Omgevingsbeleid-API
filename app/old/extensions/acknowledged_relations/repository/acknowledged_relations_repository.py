from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable


class AcknowledgedRelationsRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_by_codes(self, code_a: str, code_b: str) -> Optional[AcknowledgedRelationsTable]:
        from_code, to_code = sorted([code_a, code_b])
        stmt = select(AcknowledgedRelationsTable).filter(
            and_(
                AcknowledgedRelationsTable.From_Code == from_code,
                AcknowledgedRelationsTable.To_Code == to_code,
                AcknowledgedRelationsTable.Deleted_At == None,
                AcknowledgedRelationsTable.Denied == None,
            )
        )
        return self._db.scalars(stmt).first()

    def get_with_filters(
        self,
        code: str,
        requested_by_me: bool,
        acknowledged: Optional[bool],
        show_inactive: bool = True,
    ) -> List[AcknowledgedRelationsTable]:
        filters = []

        if requested_by_me:
            filters.append(AcknowledgedRelationsTable.Requested_By_Code == code)
        else:
            filters.append(
                or_(
                    AcknowledgedRelationsTable.From_Code == code,
                    AcknowledgedRelationsTable.To_Code == code,
                )
            )

        if acknowledged is not None:
            if acknowledged is True:
                filters.append(AcknowledgedRelationsTable.Is_Acknowledged)
            else:
                filters.append(
                    or_(
                        AcknowledgedRelationsTable.From_Acknowledged == None,
                        AcknowledgedRelationsTable.To_Acknowledged == None,
                    )
                )

        if show_inactive is False:
            filters.append(
                and_(
                    AcknowledgedRelationsTable.Deleted_At == None,
                    AcknowledgedRelationsTable.Denied == None,
                )
            )

        stmt = select(AcknowledgedRelationsTable).filter(*filters)
        rows: List[AcknowledgedRelationsTable] = self._db.scalars(stmt).all()
        return rows
