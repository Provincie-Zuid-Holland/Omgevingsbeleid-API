from typing import Dict, Set


class ObjectFieldMappingProvider:
    def __init__(self):
        self._field_mappings: Dict[str, Set[str]] = {}

    # Ideally i have the class stateless and pass all data in the constructor
    # But this class needs to exists before we can get this data
    #   as this class needs to be given to the ApiContainer from the BuildContainer before
    #   the Build Phase can calculate this data
    # Therefor we sadly fill this class with this add_object_field_mapping, which should only
    # at the build phase and after that become immutable
    def add_object_field_mapping(self, object_type: str, field_names: Set[str]) -> None:
        self._field_mappings[object_type] = field_names

    def get_valid_fields_for_type(self, object_type: str) -> Set[str]:
        fields: Set[str] = self._field_mappings.get(object_type, set())
        if not fields:
            raise RuntimeError(f"The Object_Type '{object_type}' does not exist in ObjectFieldMappingProvider")
        return fields
