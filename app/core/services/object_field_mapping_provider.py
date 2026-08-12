class ObjectFieldMappingProvider:
    def __init__(self, field_mappings: dict[str, set[str]]):
        self._field_mappings: dict[str, set[str]] = field_mappings

    def get_valid_fields_for_type(self, object_type: str) -> set[str]:
        fields: set[str] = self._field_mappings.get(object_type, set())
        if not fields:
            raise RuntimeError(f"The Object_Type '{object_type}' does not exist in ObjectFieldMappingProvider")
        return fields
