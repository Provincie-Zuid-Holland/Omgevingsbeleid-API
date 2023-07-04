import click

import app.extensions.database_migration.commands.commands as commands
from app.dynamic.extension import Extension


class DatabaseMigrationExtension(Extension):
    def register_commands(self, main_command_group: click.Group, main_config: dict):
        main_command_group.add_command(commands.initdb, "init-db")
        main_command_group.add_command(commands.dropdb, "drop-db")

        # @todo: should probable be moves
        main_command_group.add_command(commands.load_fixtures, "load-fixtures")
