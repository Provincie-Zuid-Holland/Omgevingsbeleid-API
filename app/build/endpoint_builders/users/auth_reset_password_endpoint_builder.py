from app.api.domains.users.endpoints import post_auth_reset_password_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class AuthResetPasswordEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "auth_reset_password"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_auth_reset_password_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Changes password for a user",
            tags=["Authentication"],
        )
