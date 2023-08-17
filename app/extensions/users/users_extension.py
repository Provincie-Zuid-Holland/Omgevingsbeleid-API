from typing import List

import click

import app.extensions.users.commands as commands
import app.extensions.users.endpoints as endpoints
from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.users.model import UserShort
from app.extensions.users.permission_service import main_permission_service


class UsersExtension(Extension):
    def initialize(self, main_config: dict):
        for role, permissions in main_config.get("users_permissions", {}).items():
            main_permission_service.overwrite_role(role, permissions)

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

    def register_commands(self, main_command_group: click.Group, main_config: dict):
        main_command_group.add_command(commands.create_user, "user-create")
        main_command_group.add_command(commands.reset_password, "user-reset-password")
