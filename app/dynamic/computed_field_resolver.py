from typing import Dict, List
from .config.models import ComputedField


class ComputedFieldResolver:
    def __init__(self):
        self._computed_fields: Dict[str, ComputedField] = {}

    def get(self, id: str) -> ComputedField:
        if not id in self._computed_fields:
            raise RuntimeError(f"Computed field ID '{id}' does not exist")

        return self._computed_fields[id]

    def get_all(self) -> List[ComputedField]:
        return list(self._computed_fields.values())

    def exists(self, id: str) -> bool:
        return id in self._computed_fields

    def add(self, computed_field: ComputedField):
        if self.exists(computed_field.id):
            raise RuntimeError(f"Computed field ID '{computed_field.id}' already exists")
        self._computed_fields[computed_field.id] = computed_field

    def add_many(self, computed_fields: List[ComputedField]):
        """Bulk add multiple computed fields at once"""
        for computed_field in computed_fields:
            self.add(computed_field)
