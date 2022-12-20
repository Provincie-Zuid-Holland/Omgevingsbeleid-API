from typing import Any, List
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy_utils.functions.orm import get_mapper

from app.crud.base import CRUDBase
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
            self.db.query(self.model)
            .options(
                joinedload(Beleidsmodule.Beleidskeuzes),
                joinedload(Beleidsmodule.Maatregelen),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )

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
