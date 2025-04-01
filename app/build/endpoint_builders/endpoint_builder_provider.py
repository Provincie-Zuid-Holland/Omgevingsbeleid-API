from typing import Dict, List, Optional

from app.build.endpoint_builders.endpoint_builder import EndpointBuilder


class EndpointBuilderProvider:
    def __init__(self, endpoint_builders: List[EndpointBuilder]):
        self._endpoint_builders: Dict[str, EndpointBuilder] = {
            b.get_id(): b for b in endpoint_builders
        }
    
    def get(self, builder_id: str) -> EndpointBuilder:
        if builder_id not in self._endpoint_builders:
            raise KeyError(f"EndpointBuilder with id '{builder_id}' does not exist.")
        return self._endpoint_builders[builder_id]

    def get_optional(self, builder_id: str) -> Optional[EndpointBuilder]:
        if builder_id not in self._endpoint_builders:
            raise KeyError(f"EndpointBuilder with id '{builder_id}' does not exist.")
        return self._endpoint_builders[builder_id]
