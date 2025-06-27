from app.api.domains.users.endpoints.reset_user_password_endpoint import (
    ResetPasswordResponse,
    post_reset_user_password_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ResetUserPasswordEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "reset_user_password"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_reset_user_password_endpoint,
            methods=["POST"],
            response_model=ResetPasswordResponse,
            summary=f"Reset user password",
            description=None,
            tags=["User"],
        )
