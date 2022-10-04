from datetime import datetime
from typing import Any, List, Optional, Tuple

from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Query, aliased
from sqlalchemy.sql.expression import Alias, or_

from app.crud.base import CRUDBase
from app.db.base_class import NULL_UUID
from app.models.werkingsgebied import Werkingsgebied
from app.schemas.werkingsgebied import WerkingsgebiedCreate, WerkingsgebiedUpdate


class CRUDWerkingsgebied(
    CRUDBase[Werkingsgebied, WerkingsgebiedCreate, WerkingsgebiedUpdate]
):
    def get(self, uuid: str) -> Werkingsgebied:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Werkingsgebied.Beleidskeuzes),
            )
            .filter(Werkingsgebied.UUID == uuid)
            .one()
        )

    def _build_valid_view_query(self, ID: Optional[int] = None) -> Tuple[Query, Werkingsgebied]:
        """
        Retrieve a Werkingsgebied with the 'Valid' view filters applied.
        Defaults to:

        """
        sub_query: Alias = self._build_valid_inner_query().subquery("inner")
        inner_alias: Werkingsgebied = aliased(
            element=Werkingsgebied, 
            alias=sub_query, 
            name="inner"
        )

        query: Query = (
            self.db.query(inner_alias)
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(inner_alias.Begin_Geldigheid <= datetime.utcnow())
            .filter(inner_alias.Eind_Geldigheid > datetime.utcnow())
        )

        if ID is not None:
            query = query.filter(inner_alias.ID == ID)

        return query, inner_alias

    def _build_valid_inner_query(self) -> Query:
        """
        Base valid query usable as subquery
        """
        row_number = self._add_rownumber_latest_id()
        query: Query = (
            self.db.query(Werkingsgebied, row_number)
            .filter(Werkingsgebied.UUID != NULL_UUID)
        )
        return query


werkingsgebied = CRUDWerkingsgebied(Werkingsgebied)
