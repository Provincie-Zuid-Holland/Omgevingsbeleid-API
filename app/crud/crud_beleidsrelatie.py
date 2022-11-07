from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Tuple, Type

from sqlalchemy import and_
from sqlalchemy.orm import Query, aliased, Session
from sqlalchemy.sql import label
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import Alias, func

from app.crud.base import CRUDBase, ModelType
from app.crud.crud_beleidskeuze import CRUDBeleidskeuze
from app.db.base_class import NULL_UUID
from app.models.beleidsrelatie import Beleidsrelatie
from app.schemas.beleidsrelatie import BeleidsrelatieCreate, BeleidsrelatieUpdate
from app.schemas.filters import Filters


class CRUDBeleidsrelatie(
    CRUDBase[Beleidsrelatie, BeleidsrelatieCreate, BeleidsrelatieUpdate]
):
    def __init__(self, model: Type[ModelType], db: Session, crud_beleidskeuze: CRUDBeleidskeuze):
        super(CRUDBase, self).__init__(model, db)
        self.crud_beleidskeuze = crud_beleidskeuze

    def valid(
        self,
        ID: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
        filters: Optional[Filters] = None,
    ) -> List[Beleidsrelatie]:
        """
        Retrieve valid beleidsrelaties by building valid query
        and applying filters/pagination.
        """
        # Base valid query
        query, alias = self._build_valid_view_query(ID)

        # Apply additional filters or ordering
        filtered = self._build_filtered_query(query=query, filters=filters)
        ordered = filtered.order_by(alias.ID.desc())
        query = ordered.offset(offset)

        if limit != -1:
            query = query.limit(limit)

        return query.all()

    def _build_valid_view_query(self, ID: Optional[int] = None) -> Tuple[Query, Beleidsrelatie]:
        """
        Build query with the 'Valid' view filters applied.
        Defaults to:
        - distinct ID's by latest modified
        - no null UUID row
        - Eind_Geldigheid in the future
        - Begin_Geldigheid today or in the past
        - Beleidskeuze UUIDs for valid BKs only
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("T")
        inner_alias: Beleidsrelatie = aliased(element=Beleidsrelatie, alias=sub_query, name="T")

        # only valid if refering to valid beleidskeuzes
        bk_uuids = self.crud_beleidskeuze.valid_uuids()
        bk_filter = and_(
            inner_alias.Van_Beleidskeuze_UUID.in_(bk_uuids),
            inner_alias.Naar_Beleidskeuze_UUID.in_(bk_uuids)
        )

        query: Query = (
            self.db.query(inner_alias)
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(inner_alias.Begin_Geldigheid <= datetime.utcnow())
            .filter(inner_alias.Eind_Geldigheid > datetime.utcnow())
            .filter(inner_alias.UUID != NULL_UUID)
            .filter(bk_filter)
        )

        if ID is not None:
            query = query.filter(inner_alias.ID == ID)

        return query, inner_alias


    def _build_valid_inner_query(self) -> Query:
        """
        Base valid query usable as subquery
        """
        partition: ColumnElement = func.row_number().over(
            partition_by=Beleidsrelatie.ID, order_by=Beleidsrelatie.Modified_Date.desc()
        )
        query: Query = (
            self.db.query(Beleidsrelatie, label("RowNumber", partition))
        )
        return query
