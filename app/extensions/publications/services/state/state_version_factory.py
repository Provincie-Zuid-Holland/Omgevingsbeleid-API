from typing import Dict, Type

from app.extensions.publications.services.state.state import State


class StateVersionFactory:
    def __init__(self):
        self._versions: Dict[int, Type[State]] = {}

    def add(self, state_model: Type[State]):
        schema_version: int = state_model.get_schema_version()
        self._versions[schema_version] = state_model

    def get_state_model(self, schema_version: int) -> Type[State]:
        if schema_version not in self._versions:
            raise RuntimeError(f"State schema version '{schema_version}' is not registered")
        result: Type[State] = self._versions[schema_version]
        return result
