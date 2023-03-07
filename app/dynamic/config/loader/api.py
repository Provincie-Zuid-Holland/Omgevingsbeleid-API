from typing import List

from ..models import Api, EndpointConfig


def api_loader(id: str, object_type: str, config: dict) -> Api:
    prefix: str = config.get("prefix")
    endpoints: List[EndpointConfig] = []

    for router_config in config.get("routers", []):
        prefix: str = router_config.get("prefix", "")

        for endpoint_config in router_config.get("endpoints", []):
            resolver_id: str = endpoint_config.get("resolver")
            resolver_data: dict = endpoint_config.get("resolver_data", {})
            endpoints.append(
                EndpointConfig(
                    prefix=prefix,
                    resolver_id=resolver_id,
                    resolver_data=resolver_data,
                )
            )

    return Api(
        id=id,
        object_type=object_type,
        endpoint_configs=endpoints,
    )
