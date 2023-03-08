from typing import List
from uuid import UUID

import pydantic
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher

from app.dynamic.extension import Extension
from app.dynamic.config.models import ExtensionModel
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.users.model import UserShort
import app.extensions.users.endpoints as endpoints


class UsersExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="gebruikers_short",
                name="GebruikersShort",
                pydantic_model=UserShort,
            )
        )
        models_resolver.add(
            ExtensionModel(
                id="user_short",
                name="UserShort",
                pydantic_model=UserShort,
            )
        )

    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.ListUsersEndpointResolver(),
        ]
