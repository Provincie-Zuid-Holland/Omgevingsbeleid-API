from app.api.domains.users.endpoints.get_user_endpoint import view_get_user_endpoint
from app.api.domains.users.types import User
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class GetUserEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "get_user"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=view_get_user_endpoint,
            methods=["GET"],
            response_model=User,
            summary=f"Get a user",
            description=None,
            tags=["User"],
        )
