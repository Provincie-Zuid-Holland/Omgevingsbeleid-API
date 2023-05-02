from typing import Optional, List

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable


class AcknowledgedRelationsRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_by_codes(
        self, code_a: str, code_b: str
    ) -> Optional[AcknowledgedRelationsTable]:
        from_code, to_code = sorted([code_a, code_b])
        stmt = select(AcknowledgedRelationsTable).filter(
            AcknowledgedRelationsTable.From_Code == from_code,
            AcknowledgedRelationsTable.To_Code == to_code,
        )
        maybe_relation = self._db.scalars(stmt).first()
        return maybe_relation

    def get_with_filters(
        self,
        code: str,
        requested_by_me: bool,
        acknowledged: Optional[bool],
        show_denied: bool = False,
    ) -> List[AcknowledgedRelationsTable]:
        filters = []

        if requested_by_me:
            filters.append(and_(AcknowledgedRelationsTable.Requested_By_Code == code))
        else:
            filters.append(
                or_(
                    AcknowledgedRelationsTable.From_Code == code,
                    AcknowledgedRelationsTable.To_Code == code,
                )
            )

        if acknowledged is not None:
            if acknowledged is True:
                filters.append(AcknowledgedRelationsTable.Is_Acknowledged == True)
            else:
                filters.append(AcknowledgedRelationsTable.Is_Acknowledged == False)

        if show_denied:
            filters.append(AcknowledgedRelationsTable.Is_Denied == True)

        stmt = select(AcknowledgedRelationsTable).filter(*filters)
        rows: List[AcknowledgedRelationsTable] = self._db.scalars(stmt).all()
        return rows
