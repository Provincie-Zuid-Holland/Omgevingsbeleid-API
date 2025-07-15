from typing import List
from app.api.domains.users.endpoints.edit_user_endpoint import EditUserEndpointContext, post_edit_user_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditUserEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_user"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{user_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {user_uuid} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        allowed_roles: List[str] = resolver_config.get("allowed_roles", [])

        context = EditUserEndpointContext(
            allowed_roles=allowed_roles,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(post_edit_user_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit user",
            description=None,
            tags=["User"],
        )
