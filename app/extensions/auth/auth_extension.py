import pydantic
from fastapi import APIRouter

from app.dynamic.config.models import ExtensionModel, Model
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver

from .endpoints import LoginAccessTokenEndpoint, PasswordResetEndpoint


class AuthExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        identifier_model: Model = models_resolver.get("user_login_details")
        

    def register_endpoints(
        self,
        event_dispatcher: EventDispatcher,
        models_resolver: ModelsResolver,
        router: APIRouter,
    ) -> APIRouter:
        login_endpoint: LoginAccessTokenEndpoint = LoginAccessTokenEndpoint(models_resolver)
        login_endpoint.register(router)

        password_reset_endpoint: PasswordResetEndpoint = PasswordResetEndpoint()
        password_reset_endpoint.register(router)

        return router
