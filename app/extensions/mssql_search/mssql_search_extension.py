from typing import List

import click

from app.dynamic.extension import Extension
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.converter import Converter
from app.extensions.mssql_search.commands.commands import setup_search_database
import app.extensions.mssql_search.endpoints as endpoints


class MssqlSearchExtension(Extension):
    def register_commands(self, main_command_group: click.Group):
        main_command_group.add_command(
            setup_search_database, "mssql-setup-search-database"
        )

    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.MssqlSearchEndpointResolver(),
        ]
