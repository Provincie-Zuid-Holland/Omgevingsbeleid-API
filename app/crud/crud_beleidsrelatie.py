from datetime import datetime
from typing import List, Optional, Tuple, Type

from sqlalchemy.orm import Query, Session, aliased
from sqlalchemy.sql import label
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
    def __init__(self, model: Type[ModelType], db: Session):
        super().__init__(model, db)

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
        query, inner_query = self._build_valid_view_query(ID)

        # Apply additional filters or ordering
        filtered = self._build_filtered_query(query=query, filters=filters)
        ordered = filtered.order_by(inner_query.ID.desc())
        query = ordered.offset(offset)

        if limit != -1:
            query = query.limit(limit)

        query.session = self.db
        return query.all()

    def _build_valid_view_query(
        self, ID: Optional[int] = None
    ) -> Tuple[Query, Beleidsrelatie]:
        """
        Beleidsrelaties query with the 'Valid' view filters applied.
        additional valid BK joins.
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("T")
        beleidsrelatie: Beleidsrelatie = aliased(
            element=Beleidsrelatie, alias=sub_query, name="T"
        )

        valid_bk = CRUDBeleidskeuze.valid_uuid_query_static().subquery()

        query = (
            Query(beleidsrelatie)
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(beleidsrelatie.Begin_Geldigheid <= datetime.utcnow())
            .filter(beleidsrelatie.Eind_Geldigheid > datetime.utcnow())
            .filter(beleidsrelatie.UUID != NULL_UUID)
            .filter(beleidsrelatie.Van_Beleidskeuze_UUID.in_(valid_bk))
            .filter(beleidsrelatie.Naar_Beleidskeuze_UUID.in_(valid_bk))
        )

        if ID is not None:
            query = query.filter(beleidsrelatie.ID == ID)

        return query, beleidsrelatie

    def _build_valid_inner_query(self) -> Query:
        """
        Partition latest versions by ID
        """
        partition = func.row_number().over(
            partition_by=Beleidsrelatie.ID, order_by=Beleidsrelatie.Modified_Date.desc()
        )
        return Query([Beleidsrelatie, label("RowNumber", partition)])
