from typing import Any, Dict, List, Set

from sqlalchemy.orm import Session

from app.api.domains.publications.repository.publication_object_repository import PUBLICATION_BASE_FIELDS, PublicationObjectRepository
from app.core.services.object_field_mapping_provider import ObjectFieldMappingProvider
from app.core.tables.publications import ObjectFieldMapTypeAdapter, PublicationTemplateTable, PublicationVersionTable


class PublicationObjectProvider:
    def __init__(
        self,
        publication_object_repository: PublicationObjectRepository,
        object_field_mapping_provider: ObjectFieldMappingProvider,
    ):
        self._publication_object_repository: PublicationObjectRepository = publication_object_repository
        self._object_field_mapping_provider: ObjectFieldMappingProvider = object_field_mapping_provider

    def get_objects(
        self,
        session: Session,
        publication_version: PublicationVersionTable,
    ) -> List[dict]:
        template: PublicationTemplateTable = publication_version.Publication.Template
        object_field_map: Dict[str, List[str]] = template.Object_Field_Map
        requested_fields: Set[str] = {field for field_list in object_field_map.values() for field in field_list}
        objects: List[dict] = self._publication_object_repository.fetch_objects(
            session,
            publication_version.Publication.Module_ID,
            publication_version.Module_Status.Created_Date,
            template.Object_Types,
            list(requested_fields),
        )

        objects = self._filter_object_fields(template.Object_Field_Map, objects)

        return objects

    def _filter_object_fields(self, object_field_map: Dict[str, List[str]], objects: List[dict]) -> List[dict]:
        ObjectFieldMapTypeAdapter.validate_python(object_field_map)

        result: List[dict] = []
        for obj in objects:
            obj_type: str = obj["Object_Type"]
            type_specific_fields: Set[str] = set(object_field_map.get(obj_type, []))
            allowed_fields: Set[str] = PUBLICATION_BASE_FIELDS | set(["Module_ID"]) | type_specific_fields

            # @NOTE: I'm not sure anymore why we keep fields with underscores here
            cleaned: dict = {
                key: value
                for key, value in obj.items()
                if key in allowed_fields or (isinstance(key, str) and key.startswith("_"))
            }

            result.append(cleaned)

        return result
