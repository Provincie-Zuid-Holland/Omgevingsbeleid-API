from app.api.domains.users.endpoints import post_auth_login_access_token_endpoint
from app.api.domains.users.types import AuthToken
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class AuthLoginAccessTokenEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "auth_login_access_token"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_auth_login_access_token_endpoint,
            methods=["POST"],
            response_model=AuthToken,
            summary=f"Login an user and receive a JWT token",
            tags=["Authentication"],
        )
