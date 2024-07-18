from typing import List

import click

import app.extensions.mssql_search.endpoints as endpoints
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.mssql_search.commands.commands import setup_search_database_curried


class MssqlSearchExtension(Extension):
    def register_commands(self, main_command_group: click.Group, main_config: dict):
        main_command_group.add_command(setup_search_database_curried(main_config), "mssql-setup-search-database")

    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.MssqlSearchEndpointResolver(),
            endpoints.MssqlValidSearchEndpointResolver(),
        ]
