from datetime import datetime
from typing import Any, List, Optional, Tuple

from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Query, aliased
from sqlalchemy.sql import union
from sqlalchemy.sql.expression import Alias, or_

from app.crud.base import CRUDBase
from app import crud, models
from app.db.base_class import NULL_UUID
from app.db.session import engine
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

    def _build_valid_view_query(
        self, ID: Optional[int] = None
    ) -> Tuple[Query, Werkingsgebied]:
        """
        Retrieve a Werkingsgebied with the 'Valid' view filters applied.
        Defaults to:
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("inner")
        inner_alias: Werkingsgebied = aliased(
            element=Werkingsgebied, alias=sub_query, name="inner"
        )

        valid_uuid_filter = self._build_valid_uuid_filter(alias=inner_alias)

        query: Query = (
            self.db.query(inner_alias)
            .outerjoin(models.Beleidskeuze_Werkingsgebieden)
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(inner_alias.Begin_Geldigheid <= datetime.utcnow())
            .filter(inner_alias.Eind_Geldigheid > datetime.utcnow())
            .filter(valid_uuid_filter)
        )

        if ID is not None:
            query = query.filter(inner_alias.ID == ID)

        return query, inner_alias

    def _build_valid_inner_query(self) -> Query:
        """
        Base valid query usable as subquery
        """
        row_number = self._add_rownumber_latest_id()
        query: Query = self.db.query(Werkingsgebied, row_number).filter(
            Werkingsgebied.UUID != NULL_UUID
        )
        return query

    def _build_valid_uuid_filter(self, alias=None):
        """
        Build relationship sub filter list of valid werkingsgebied
        UUIDs in valid maatregelen or valid beleidskeuzes
        """
        valid_maatregel_gebieden = crud.maatregel.valid_werkingsgebied_uuids()
        valid_beleidskeuzes = crud.beleidskeuze.valid_uuids()

        if alias is None:
            filter = or_(
                Werkingsgebied.UUID.in_(valid_maatregel_gebieden),
                models.Beleidskeuze_Werkingsgebieden.Beleidskeuze_UUID.in_(
                    valid_beleidskeuzes
                ),
            )
        else:
            filter = or_(
                alias.UUID.in_(valid_maatregel_gebieden),
                models.Beleidskeuze_Werkingsgebieden.Beleidskeuze_UUID.in_(
                    valid_beleidskeuzes
                ),
            )

        return filter


werkingsgebied = CRUDWerkingsgebied(Werkingsgebied)
