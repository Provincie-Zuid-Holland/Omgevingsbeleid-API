from typing import Any, Dict, List, Set

from sqlalchemy.orm import Session

from app.api.domains.publications.repository.publication_object_repository import PublicationObjectRepository
from app.core.services.object_field_mapping_provider import ObjectFieldMappingProvider
from app.core.tables.publications import PublicationVersionTable


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
        objects: List[dict] = self._publication_object_repository.fetch_objects(
            session,
            publication_version.Publication.Module_ID,
            publication_version.Module_Status.Created_Date,
            publication_version.Publication.Template.Object_Types,
            publication_version.Publication.Template.Field_Map,
        )

        objects = self._filter_object_fields(objects)

        return objects

    def _filter_object_fields(self, objects: List[dict]) -> List[dict]:
        filtered_objects: List[dict] = []

        for obj in objects:
            object_type = obj.get("Object_Type")
            if not object_type:
                raise RuntimeError("Expecting 'Object_Type' in the object's fields")

            valid_fields: Set[str] = self._object_field_mapping_provider.get_valid_fields_for_type(object_type)

            filtered_obj: Dict[str, Any] = {}
            for key, value in obj.items():
                # Always keep system fields that start with underscore or other special fields
                if key.startswith("_") or key == "Module_ID":
                    filtered_obj[key] = value
                elif key in valid_fields:
                    filtered_obj[key] = value

            filtered_objects.append(filtered_obj)

        return filtered_objects
