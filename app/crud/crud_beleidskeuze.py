from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Query, aliased
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.sql import Subquery
from sqlalchemy.sql.expression import Alias, or_
from sqlalchemy_utils import get_mapper

from app.core.exceptions import DatabaseError
from app.crud.base import GeoCRUDBase
from app.db.base_class import NULL_UUID
from app.models.beleidskeuze import Beleidskeuze
from app.models.werkingsgebied import Beleidskeuze_Werkingsgebieden
from app.schemas.beleidskeuze import BeleidskeuzeCreate, BeleidskeuzeUpdate
from app.schemas.beleidskeuze import Beleidskeuze as schema_beleidskeuze
from app.schemas.filters import Filters

LINK_DESCRIPTION = "Koppeling_Omschrijving"
ASSOC_UUID_KEY = "Beleidskeuze_UUID"


class CRUDBeleidskeuze(
    GeoCRUDBase[Beleidskeuze, BeleidskeuzeCreate, BeleidskeuzeUpdate]
):
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

    def update(
        self,
        current_bk: Beleidskeuze,
        obj_in: Union[BeleidskeuzeUpdate, Dict[str, Any]],
        by_uuid: str,
    ) -> Beleidskeuze:
        """
        Patches a beleidskeuze.

        Since updating/patching creates a new object with a different UUID
        in our database, we require all relationships (existing and new)
        to be re-initialized instead of updated.
        """
        obj_data = jsonable_encoder(current_bk)
        bk_mapper = get_mapper(current_bk)
        bk_base_attrs = bk_mapper.columns.keys()

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        # Build updated BK base data
        new_bk_data = dict()
        for field in bk_base_attrs:
            if field in update_data:
                new_bk_data[field] = update_data[field]
            else:
                new_bk_data[field] = obj_data[field]

        # New BK object (no relations)
        new_bk_data["UUID"] = uuid4()
        new_bk_data["Modified_Date"] = datetime.now()
        new_bk_data["Modified_By_UUID"] = by_uuid
        new_bk = Beleidskeuze(**new_bk_data)

        # Create relationship assoc rows
        updated_associations = self.update_association_objects(
            current_bk, new_bk, update_data
        )

        try:
            self.db.add(new_bk)  # Base object
            for assoc_obj in updated_associations:  # Relations
                self.db.add(assoc_obj)
        except:
            self.db.rollback()
            raise DatabaseError()

        self.db.commit()
        self.db.refresh(new_bk)
        return new_bk

    def update_association_objects(
        self, current_bk: Beleidskeuze, new_bk: Beleidskeuze, update_data: dict
    ) -> List[Any]:
        """
        "Update" relations by creating new association objects as specified in the request data,
        or re-create existing relationships with the updated object UUID.

        Returns a list of association objects.
        """
        relationships = Beleidskeuze.get_relationships()
        fork = Beleidskeuze.get_foreign_column_keys()
        assoc_relations = [i for i in relationships.keys() if i not in fork]

        result = list()

        for relation_key in assoc_relations:
            mapper: Mapper = get_mapper(relationships[relation_key].entity.class_)
            assoc_table_keys = mapper.relationships.keys()

            LINK_DESCRIPTION = "Koppeling_Omschrijving"
            ASSOC_UUID_KEY = "Beleidskeuze_UUID"
            REL_UUID_KEY = f"{assoc_table_keys[1]}_UUID"  # Get name of relationship foreign key to update

            if relation_key in update_data:
                for update_item in update_data[relation_key]:
                    # Build new association object
                    assoc_obj = mapper.class_()  # Beleidskeuze_* Instance
                    setattr(assoc_obj, ASSOC_UUID_KEY, new_bk.UUID)
                    setattr(assoc_obj, REL_UUID_KEY, update_item["UUID"])
                    setattr(assoc_obj, LINK_DESCRIPTION, update_item[LINK_DESCRIPTION])
                    result.append(assoc_obj)
            else:
                # copy existing relationships
                for rel in getattr(current_bk, relation_key):
                    assoc_obj = mapper.class_()  # Beleidskeuze_* Instance
                    setattr(assoc_obj, ASSOC_UUID_KEY, new_bk.UUID)
                    setattr(assoc_obj, REL_UUID_KEY, getattr(rel, REL_UUID_KEY))
                    setattr(assoc_obj, LINK_DESCRIPTION, getattr(rel, LINK_DESCRIPTION))
                    result.append(assoc_obj)

        return result

    # Overwritten to eager join relations
    def _build_latest_view_filter(
        self, all: bool, filters: Optional[Filters] = None
    ) -> Query:
        """
        Retrieve latest beleidskeuzes and eager join relations
        Filters applied:
        - window distinct ID's by latest modified
        - no null UUID rows
        - Eind_Geldigheid in the future

        **Parameters**

        * `all`: If true, omits Eind_Geldigheid check
        """

        row_number = self._add_rownumber_latest_id()
        sub_query: Subquery = self.db.query(Beleidskeuze, row_number).subquery("inner")

        model_alias: Beleidskeuze = aliased(
            element=Beleidskeuze, alias=sub_query, name="inner", adapt_on_names=True
        )

        last_modified_id_filter = sub_query.c.get("RowNumber") == 1

        query: Query = (
            self.db.query(model_alias)
            .filter(last_modified_id_filter)
            .filter(model_alias.UUID != NULL_UUID)
        )

        eager_load_relations = [
            joinedload(model_alias.Ambities),
            joinedload(model_alias.Belangen),
            joinedload(model_alias.Beleidsdoelen),
            joinedload(model_alias.Beleidsprestaties),
            joinedload(model_alias.Maatregelen),
            joinedload(model_alias.Themas),
            joinedload(model_alias.Verordeningen),
            joinedload(model_alias.Werkingsgebieden),
            joinedload(model_alias.Beleidsmodules),
        ]

        query = query.options(*eager_load_relations)

        if not all:
            query = query.filter(model_alias.Eind_Geldigheid > datetime.utcnow())

        query = self._build_filtered_query(
            query=query, model=model_alias, filters=filters
        )

        return query.order_by(model_alias.ID.desc())

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
    ) -> Tuple[Query, Beleidskeuze]:
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
        inner_alias: Beleidskeuze = aliased(
            element=Beleidskeuze, alias=sub_query, name="inner"
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
            self.db.query(Beleidskeuze, row_number)
            .filter(Beleidskeuze.Status == "Vigerend")
            .filter(Beleidskeuze.UUID != NULL_UUID)
            .filter(Beleidskeuze.Begin_Geldigheid <= datetime.utcnow())
        )
        return query

    def fetch_in_geo(self, area_uuid: List[str], limit: int) -> List[Beleidskeuze]:
        """
        Retrieve the instances of this entity linked
        to the IDs of provided geological areas.
        """
        filter_list = [
            (Beleidskeuze_Werkingsgebieden.Werkingsgebied_UUID == uuid)
            for uuid in area_uuid
        ]

        # Query using the geo UUID in assoc table
        result = (
            self.db.query(Beleidskeuze_Werkingsgebieden)
            .options(joinedload(Beleidskeuze_Werkingsgebieden.Beleidskeuze))
            .filter(or_(*filter_list))
            .limit(limit)
            .all()
        )

        if result is None:
            return []

        def beleidskeuze_mapper(association_object: Beleidskeuze_Werkingsgebieden):
            # return beleidskeuzes but keep Gebied field
            # to return in GeoSearchResult response
            mapped = association_object.Beleidskeuze
            setattr(mapped, "Gebied", association_object.Werkingsgebied_UUID)
            return mapped

        return list(map(beleidskeuze_mapper, result))

    def as_geo_schema(self, model: Beleidskeuze):
        return schema_beleidskeuze.from_orm(model)