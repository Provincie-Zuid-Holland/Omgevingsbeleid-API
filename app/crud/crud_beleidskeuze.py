from datetime import datetime
from typing import Any, List, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Query, Session, aliased, load_only
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import ColumnElement, func
from sqlalchemy.sql.expression import label, or_

from app import models
from app.crud.base import CRUDBase
from app.db.base_class import NULL_UUID
from app.models.beleidskeuze import Beleidskeuze
from app.schemas.beleidskeuze import BeleidskeuzeCreate, BeleidskeuzeUpdate
from app.schemas.filters import Filters


class CRUDBeleidskeuze(CRUDBase[Beleidskeuze, BeleidskeuzeCreate, BeleidskeuzeUpdate]):
    def create(self, *, obj_in: BeleidskeuzeCreate, by_uuid: str) -> Beleidskeuze:
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

    # Status check for Beleidskeuzes
    def _build_valid_view_filter(
        self,
        ID: Optional[int] = None,
        filters: Optional[Filters] = None,
        as_subquery: Optional[bool] = False,
    ) -> Query:
        """
        Retrieve a model with the 'Valid' view filters applied.
        Defaults to:
        - distinct ID's by latest modified
        - no null UUID row
        - Vigerend only
        - Eind_Geldigheid in the future
        - Begin_Geldigheid today or in the past
        """
        row_number = self._add_rownumber_latest_id()

        sub_query: Query = (
            self.db.query(Beleidskeuze, row_number)
            .filter(Beleidskeuze.Status == "Vigerend")
            .filter(Beleidskeuze.UUID != NULL_UUID)
            .filter(Beleidskeuze.Begin_Geldigheid <= datetime.utcnow())
            .subquery("inner")
        )

        model_alias: AliasedClass = aliased(
            element=Beleidskeuze, alias=sub_query, name="inner"
        )

        query: Query = (
            self.db.query(model_alias)
            .filter(sub_query.c.RowNumber == 1)
            .filter(model_alias.Eind_Geldigheid > datetime.utcnow())
        )

        if as_subquery:
            return query.subquery()

        if ID is not None:
            query = query.filter(model_alias.ID == ID)

        query = self._build_filtered_query(
            query=query, model=model_alias, filters=filters
        )

        return query.order_by(model_alias.ID.desc())

    def fetch_in_geo(self, area_uuid: List[str], limit: int) -> Any:
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


beleidskeuze = CRUDBeleidskeuze(Beleidskeuze)
