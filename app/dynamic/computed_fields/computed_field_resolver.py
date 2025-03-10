from typing import Dict, List

from app.dynamic.computed_fields.handler_context import ComputedFieldHandlerCallable
from app.dynamic.computed_fields.models import ComputedField


class ComputedFieldResolver:
    def __init__(self):
        self._computed_fields: Dict[str, ComputedField] = {}
        self._handlers: Dict[str, ComputedFieldHandlerCallable] = {}

    def get(self, id: str) -> ComputedField:
        if id not in self._computed_fields:
            raise RuntimeError(f"Computed field ID '{id}' does not exist")

        return self._computed_fields[id]

    def get_all(self) -> List[ComputedField]:
        return list(self._computed_fields.values())

    def get_by_ids(self, ids: List[str]) -> List[ComputedField]:
        return [field for field in self.get_all() if field.id in ids]

    def exists(self, id: str) -> bool:
        return id in self._computed_fields

    def add(self, computed_field: ComputedField):
        if self.exists(computed_field.id):
            raise RuntimeError(f"Computed field ID '{computed_field.id}' already exists")
        self._computed_fields[computed_field.id] = computed_field

    def add_many(self, computed_fields: List[ComputedField]):
        for computed_field in computed_fields:
            self.add(computed_field)

    def add_handler(self, id: str, handler: ComputedFieldHandlerCallable):
        if id in self._handlers:
            raise RuntimeError(f"Handler ID '{id}' already exists")
        self._handlers[id] = handler

    def get_handler(self, id: str) -> ComputedFieldHandlerCallable:
        if id not in self._handlers:
            raise RuntimeError(f"Handler ID '{id}' does not exist")
        return self._handlers[id]

    def handler_exists(self, id: str) -> bool:
        return id in self._handlers
