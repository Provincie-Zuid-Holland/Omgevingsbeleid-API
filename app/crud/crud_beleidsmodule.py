from datetime import datetime
from typing import Any, List
from uuid import uuid4
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy_utils.functions.orm import get_mapper

from app.crud.base import CRUDBase
from app.models.base import find_mtm_map
from app.models.beleidsmodule import Beleidsmodule
from app.schemas.beleidsmodule import BeleidsmoduleCreate, BeleidsmoduleUpdate


class CRUDBeleidsmodule(
    CRUDBase[Beleidsmodule, BeleidsmoduleCreate, BeleidsmoduleUpdate]
):
    def get(self, uuid: str) -> Beleidsmodule:
        """
        Get by UUID and eager load relations
        """
        return (
            self.db.query(Beleidsmodule)
            .options(
                joinedload(Beleidsmodule.Beleidskeuzes),
                joinedload(Beleidsmodule.Maatregelen),
            )
            .filter(Beleidsmodule.UUID == uuid)
            .one()
        )

    # Overwritten from base to allow relationships on create
    def create(self, *, obj_in: BeleidsmoduleCreate, by_uuid: str) -> Beleidsmodule:
        """
        Create new Beleidsmodule.
        Beleidsmodule entity allows creation to include new relationships
        when listed in the request body.
        """
        obj_in_data = jsonable_encoder(
            obj_in,
            custom_encoder={
                datetime: lambda dt: dt,
            },
        )
        request_time = datetime.now()

        # First handle base attrs
        base_attrs = Beleidsmodule.get_base_column_keys()
        base_obj = {}
        for key, value in obj_in_data.items():
            if key in base_attrs:
                base_obj[key] = value

        base_obj["UUID"] = uuid4()
        base_obj["Created_By_UUID"] = by_uuid
        base_obj["Modified_By_UUID"] = by_uuid
        base_obj["Created_Date"] = request_time
        base_obj["Modified_Date"] = request_time

        db_obj = Beleidsmodule(**base_obj)

        # Create relationship assoc rows
        assoc_objects = self.create_association_objects(db_obj, obj_in_data)

        try:
            self.db.add(db_obj)  # Base object
            for assoc_obj in assoc_objects:  # Relations
                self.db.add(assoc_obj)
        except:
            self.db.rollback()
            raise DatabaseError()

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    # overwritten to allow relationships on create
    def create_association_objects(
        self, new_module: Beleidsmodule, obj_data: dict
    ) -> List[Any]:
        """
        Returns a list of association objects to create relations
        """
        relationships = Beleidsmodule.get_relationships()
        fork = Beleidsmodule.get_foreign_column_keys()
        assoc_relations = [i for i in relationships.keys() if i not in fork]

        result = list()

        for relation_key in assoc_relations:
            assoc_class = relationships[relation_key].entity.class_
            mtm_class = find_mtm_map(assoc_class)

            if relation_key in obj_data:
                if obj_data[relation_key]:
                    for rel_item in obj_data[relation_key]:
                        assoc_obj = assoc_class()  # Beleidsmodule* Instance
                        setattr(assoc_obj, mtm_class.left.key, new_module.UUID)
                        setattr(assoc_obj, mtm_class.right.key, rel_item["UUID"])
                        setattr(
                            assoc_obj,
                            mtm_class.description,
                            rel_item[mtm_class.description],
                        )
                        result.append(assoc_obj)

        return result

    # Overwritten for correct beleidsmodule relationship updates
    def update_association_objects(
        self, current_obj: Beleidsmodule, new_obj: Beleidsmodule, update_data: dict
    ) -> List[Any]:
        """
        "Update" relations by creating new association objects as specified in the request data,
        or re-create existing relationships with the updated object UUID.

        Returns a list of association objects.
        """
        relationships = Beleidsmodule.get_relationships()
        fork = Beleidsmodule.get_foreign_column_keys()
        assoc_relations = [i for i in relationships.keys() if i not in fork]

        result = list()

        for relation_key in assoc_relations:
            mapper: Mapper = get_mapper(relationships[relation_key].entity.class_)
            assoc_table_keys = mapper.relationships.keys()

            LINK_DESCRIPTION = "Koppeling_Omschrijving"
            ASSOC_UUID_KEY = "Beleidsmodule_UUID"
            REL_UUID_KEY = f"{assoc_table_keys[1]}_UUID"

            if relation_key in update_data:
                for update_item in update_data[relation_key]:
                    # Build new association object
                    assoc_obj = mapper.class_()  # Beleidskeuze_* Instance
                    setattr(assoc_obj, ASSOC_UUID_KEY, str(new_obj.UUID).upper())
                    setattr(assoc_obj, REL_UUID_KEY, update_item["UUID"])
                    setattr(assoc_obj, LINK_DESCRIPTION, update_item[LINK_DESCRIPTION])
                    result.append(assoc_obj)
            else:
                # copy existing relationships
                for rel in getattr(current_obj, relation_key):
                    assoc_obj = mapper.class_()  # Beleidskeuze_* Instance
                    setattr(assoc_obj, ASSOC_UUID_KEY, str(new_obj.UUID))
                    setattr(assoc_obj, REL_UUID_KEY, getattr(rel, REL_UUID_KEY))
                    setattr(assoc_obj, LINK_DESCRIPTION, getattr(rel, LINK_DESCRIPTION))
                    result.append(assoc_obj)

        return result
