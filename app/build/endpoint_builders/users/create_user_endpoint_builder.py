from typing import List
from app.api.domains.users.endpoints.create_user_endpoint import (
    CreateUserEndpointContext,
    UserCreateResponse,
    post_create_user_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreateUserEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_user"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        allowed_roles: List[str] = resolver_config.get("allowed_roles", [])

        context = CreateUserEndpointContext(
            allowed_roles=allowed_roles,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(post_create_user_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=UserCreateResponse,
            summary=f"Create new user",
            description=None,
            tags=["User"],
        )
