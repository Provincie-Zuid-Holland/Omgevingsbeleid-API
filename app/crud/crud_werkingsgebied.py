from datetime import datetime
from typing import Optional, Tuple, Type

from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Query, aliased, Session
from sqlalchemy.sql.expression import Alias, or_

from app.crud.base import CRUDBase, ModelType
from app import models
from app.db.base_class import NULL_UUID
from app.models.werkingsgebied import Werkingsgebied
from app.schemas.werkingsgebied import WerkingsgebiedCreate, WerkingsgebiedUpdate
from app.crud import CRUDBeleidskeuze, CRUDMaatregel


class CRUDWerkingsgebied(
    CRUDBase[Werkingsgebied, WerkingsgebiedCreate, WerkingsgebiedUpdate]
):
    def __init__(
        self,
        model: Type[ModelType],
        db: Session,
        crud_beleidskeuze: CRUDBeleidskeuze,
        crud_maatregel: CRUDMaatregel,
    ):
        super(CRUDBase, self).__init__(model, db)
        self.crud_beleidskeuze = crud_beleidskeuze
        self.crud_maatregel = crud_maatregel

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
        valid_maatregel_gebieden = self.crud_maatregel.valid_werkingsgebied_uuids()
        valid_beleidskeuzes = self.crud_beleidskeuze.valid_uuids()

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
