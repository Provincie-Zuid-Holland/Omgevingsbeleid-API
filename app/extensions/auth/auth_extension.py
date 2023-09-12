import pydantic
from fastapi import APIRouter

from app.dynamic.config.models import ExtensionModel, Model
from app.dynamic.converter import Converter
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver

from .endpoints import LoginAccessTokenEndpoint, PasswordResetEndpoint


class AuthExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        identifier_model: Model = models_resolver.get("user_short")
        models_resolver.add(
            ExtensionModel(
                id="auth_token",
                name="AuthToken",
                pydantic_model=pydantic.create_model(
                    "AuthToken",
                    **{
                        "access_token": (str, pydantic.Field()),
                        "token_type": (str, pydantic.Field()),
                        "identifier": (
                            identifier_model.pydantic_model,
                            pydantic.Field(),
                        ),
                    },
                ),
            ),
        )

    def register_endpoints(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        router: APIRouter,
    ) -> APIRouter:
        login_endpoint: LoginAccessTokenEndpoint = LoginAccessTokenEndpoint(models_resolver)
        login_endpoint.register(router)

        password_reset_endpoint: PasswordResetEndpoint = PasswordResetEndpoint()
        password_reset_endpoint.register(router)

        return router
