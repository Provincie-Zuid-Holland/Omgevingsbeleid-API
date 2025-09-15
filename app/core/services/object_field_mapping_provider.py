from typing import Dict, Set


class ObjectFieldMappingProvider:
    def __init__(self, field_mappings: Dict[str, Set[str]]):
        self._field_mappings: Dict[str, Set[str]] = field_mappings

    def get_valid_fields_for_type(self, object_type: str) -> Set[str]:
        fields: Set[str] = self._field_mappings.get(object_type, set())
        if not fields:
            raise RuntimeError(f"The Object_Type '{object_type}' does not exist in ObjectFieldMappingProvider")
        return fields
