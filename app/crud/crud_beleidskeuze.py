from datetime import datetime
from typing import List, Optional, Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Query, aliased
from sqlalchemy.sql.expression import Alias, or_

from app.crud.base import GeoCRUDBase
from app.db.base_class import NULL_UUID
from app import schemas
from app import models


class CRUDBeleidskeuze(
    GeoCRUDBase[
        models.Beleidskeuze, schemas.BeleidskeuzeCreate, schemas.BeleidskeuzeUpdate
    ]
):
    def create(
        self, *, obj_in: schemas.BeleidskeuzeCreate, by_uuid: str
    ) -> models.Beleidskeuze:
        obj_in_data = jsonable_encoder(
            obj_in,
            custom_encoder={
                datetime: lambda dt: dt,
            },
        )

        request_time = datetime.now()

        obj_in_data["Created_By_UUID"] = by_uuid
        obj_in_data["Modified_By_UUID"] = by_uuid
        obj_in_data["Created_Date"] = request_time
        obj_in_data["Modified_Date"] = request_time

        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def valid_uuids(self) -> List[str]:
        """
        Retrieve list of only valid UUIDs in beleidskeuzes
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("inner")
        query = (
            self.db.query(sub_query.c.get("UUID"))
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(sub_query.c.get("Eind_Geldigheid") > datetime.utcnow())
        )

        return [bk.UUID for bk in query]

    def _build_valid_view_query(
        self, ID: Optional[int] = None
    ) -> Tuple[Query, models.Beleidskeuze]:
        """
        Retrieve a model with the 'Valid' view filters applied.
        Defaults to:
        - distinct ID's by latest modified
        - no null UUID row
        - Vigerend only
        - Eind_Geldigheid in the future
        - Begin_Geldigheid today or in the past
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("inner")
        inner_alias: models.Beleidskeuze = aliased(
            element=models.Beleidskeuze, alias=sub_query, name="inner"
        )

        query: Query = (
            self.db.query(inner_alias)
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(inner_alias.Eind_Geldigheid > datetime.utcnow())
        )

        if ID is not None:
            query = query.filter(inner_alias.ID == ID)

        return query, inner_alias

    # Extra status vigerend check for Beleidskeuzes
    def _build_valid_inner_query(self) -> Query:
        """
        Base valid query usable as subquery
        """
        row_number = self._add_rownumber_latest_id()
        query: Query = (
            self.db.query(models.Beleidskeuze, row_number)
            .filter(models.Beleidskeuze.Status == "Vigerend")
            .filter(models.Beleidskeuze.UUID != NULL_UUID)
            .filter(models.Beleidskeuze.Begin_Geldigheid <= datetime.utcnow())
        )
        return query

    def fetch_in_geo(
        self, area_uuid: List[str], limit: int
    ) -> List[models.Beleidskeuze]:
        """
        Retrieve the instances of this entity linked
        to the IDs of provided geological areas.
        """
        association = models.Beleidskeuze_Werkingsgebieden
        filter_list = [(association.Werkingsgebied_UUID == uuid) for uuid in area_uuid]

        # Query using the geo UUID in assoc table
        result = (
            self.db.query(association)
            .options(joinedload(association.Beleidskeuze))
            .filter(or_(*filter_list))
            .limit(limit)
            .all()
        )

        if result is None:
            return []

        def beleidskeuze_mapper(association_object: association):
            # return beleidskeuzes but keep Gebied field
            # to return in GeoSearchResult response
            mapped = association_object.Beleidskeuze
            setattr(mapped, "Gebied", association_object.Werkingsgebied_UUID)
            return mapped

        return list(map(beleidskeuze_mapper, result))

    def as_geo_schema(self, model: models.Beleidskeuze):
        return schemas.Beleidskeuze.from_orm(model)
