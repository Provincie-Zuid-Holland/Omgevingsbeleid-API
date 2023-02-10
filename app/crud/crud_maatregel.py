from datetime import datetime
from typing import Any, List, Union
from sqlalchemy import func

from sqlalchemy.orm import Query, aliased
from sqlalchemy.sql import Alias, label

from app.crud.base import GeoCRUDBase
from app.db.base_class import NULL_UUID
from app import models, schemas
from app.models.base import find_mtm_map
from app.schemas.filters import Filter, FilterCombiner, Filters
from app.schemas.maatregel import Maatregel


class CRUDMaatregel(
    GeoCRUDBase[models.Maatregel, schemas.MaatregelCreate, schemas.MaatregelUpdate]
):
    def get(self, uuid: str) -> models.Maatregel:
        return self.db.query(self.model).filter(self.model.UUID == uuid).one()

    # Overwritten from base to ensure correct mapping of
    # Beleidsmodule relations when updating
    def update_association_objects(
        self, current_bk: models.Maatregel, new_bk: models.Maatregel, update_data: dict
    ) -> List[Any]:
        """
        "Update" relations by creating new association objects as specified in the request data,
        or re-create existing relationships with the updated object UUID.

        Returns a list of association objects.
        """
        relationships = models.Maatregel.get_relationships()
        fork = models.Maatregel.get_foreign_column_keys()
        assoc_relations = [i for i in relationships.keys() if i not in fork]

        result = list()

        for relation_key in assoc_relations:
            assoc_class = relationships[relation_key].entity.class_
            mtm_class = find_mtm_map(assoc_class)

            if relation_key in update_data:
                # Build newly added relations in update request
                for update_item in update_data[relation_key]:
                    assoc_obj = assoc_class()  # Beleidskeuze_* Instance
                    setattr(assoc_obj, mtm_class.left.key, new_bk.UUID)
                    setattr(assoc_obj, mtm_class.right.key, update_item["UUID"])
                    setattr(
                        assoc_obj,
                        mtm_class.description,
                        update_item[mtm_class.description],
                    )
                    result.append(assoc_obj)
            else:
                # Copy any existing relationships
                for rel in getattr(current_bk, relation_key):
                    assoc_obj = assoc_class()  # Beleidskeuze_* Instance
                    # create relation row with new object UUID
                    setattr(assoc_obj, mtm_class.left.key, new_bk.UUID)
                    setattr(
                        assoc_obj,
                        mtm_class.right.key,
                        getattr(rel, mtm_class.right.key),
                    )

                    if relation_key == "Beleidsmodules":
                        # Switched column order for beleidsmodules
                        setattr(
                            assoc_obj,
                            mtm_class.left.key,
                            getattr(rel, mtm_class.left.key),
                        )
                        setattr(assoc_obj, mtm_class.right.key, new_bk.UUID)

                    setattr(
                        assoc_obj,
                        mtm_class.description,
                        getattr(rel, mtm_class.description),
                    )
                    result.append(assoc_obj)

        return result

    def valid_uuids(self, as_query: bool = False) -> Union[List[str], Query]:
        """
        Retrieve list of only valid UUIDs in Maatregelen
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("inner")
        query = (
            self.db.query(sub_query.c.get("UUID"))
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(sub_query.c.get("Eind_Geldigheid") > datetime.utcnow())
        )
        if as_query:
            return query

        return [bk.UUID for bk in query]

    def valid_werkingsgebied_uuids(self) -> List[str]:
        """
        Retrieve list of only gebied UUIDs in valid Maatregelen
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("inner")
        query = (
            self.db.query(sub_query.c.get("Gebied"))
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(sub_query.c.get("Eind_Geldigheid") > datetime.utcnow())
        )

        return [maatregel.Gebied for maatregel in query]

    # Extra status vigerend check for Maatregelen
    def _build_valid_inner_query(self) -> Query:
        """
        Base valid query usable as subquery
        """
        row_number = self._add_rownumber_latest_id()
        query: Query = (
            self.db.query(models.Maatregel, row_number)
            .filter(models.Maatregel.Status == "Vigerend")
            .filter(models.Maatregel.UUID != NULL_UUID)
            .filter(models.Maatregel.Begin_Geldigheid <= datetime.utcnow())
        )
        return query

    def fetch_in_geo(self, area_uuid: List[str], limit: int) -> List[models.Maatregel]:
        """
        Retrieve the instances of this entity linked
        to the IDs of provided geological areas.
        """
        col = models.Maatregel.Gebied_UUID
        filters = [Filter(key=col.key, value=id) for id in area_uuid]
        area_filter = Filters()
        area_filter._append_clause(combiner=FilterCombiner.OR, items=filters)

        return self.valid(filters=area_filter, limit=limit)

    def as_geo_schema(self, model: models.Maatregel):
        return schemas.Maatregel.from_orm(model)

    @classmethod
    def valid_view_static(cls, alias_name="subq") -> Maatregel:
        """
        Helper function to return the "Valid" filter as a subquery
        to be added to other queries.

        Retrieves only uuids, can be used to inner join to an existing query.
        """
        partition = func.row_number().over(
            partition_by=models.Maatregel.ID,
            order_by=models.Maatregel.Modified_Date.desc(),
        )
        row_number = label("RowNumber", partition)

        subq = (
            Query([models.Maatregel, row_number])
            .filter(models.Maatregel.UUID != NULL_UUID)
            .filter(models.Maatregel.Begin_Geldigheid <= datetime.utcnow())
            .filter(models.Maatregel.Status == "Vigerend")
            .subquery("inner")
        )

        inner_alias: models.Maatregel = aliased(
            element=models.Maatregel, alias=subq, name="inner"
        )

        valid_query = (
            Query(inner_alias)
            .filter(subq.c.get("RowNumber") == 1)
            .filter(subq.c.get("Eind_Geldigheid") > datetime.utcnow())
        )

        sub_query = valid_query.subquery()
        return aliased(element=models.Maatregel, alias=sub_query, name=alias_name)
