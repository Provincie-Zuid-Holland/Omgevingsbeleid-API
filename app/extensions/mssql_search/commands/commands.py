from typing import Set

import click
from sqlalchemy import DDL, inspect, text
from sqlalchemy.orm import Session

from app.core.db.session import SessionLocalWithAutoCommit
from app.core.settings import settings
from app.extensions.mssql_search.config.stopwords import stopwords


def _reset_fulltext_index(db: Session, table_name: str, columns: Set[str]):
    # Check is this table already has a search index set up
    result = db.execute(text(f"SELECT * FROM sys.fulltext_indexes WHERE object_id = object_id('{table_name}');"))
    exists = bool(result.all())
    if exists:
        db.execute(DDL(f"DROP FULLTEXT INDEX ON {table_name}"))

    if not columns:
        return

    languages_columns: Set[str] = {f"{column} Language 1043" for column in columns}

    inspector = inspect(db.bind)
    primary_key_columns = inspector.get_pk_constraint(table_name)
    primary_key_name = primary_key_columns["name"]

    query = f"""
        CREATE FULLTEXT INDEX ON {table_name} (
            {', '.join(languages_columns)}
        )
        KEY INDEX {primary_key_name}
        ON {settings.MSSQL_SEARCH_FTC_NAME}
        WITH CHANGE_TRACKING = AUTO, STOPLIST = {settings.MSSQL_SEARCH_STOPLIST_NAME}
    """
    db.execute(text(query))


def setup_search_database_curried(main_config: dict):
    @click.command()
    def setup_search_database():
        click.echo("Initialized search tables")

        with SessionLocalWithAutoCommit() as db:
            # Create stoplist
            result = db.execute(
                text(f"SELECT name FROM sys.fulltext_stoplists WHERE name = '{settings.MSSQL_SEARCH_STOPLIST_NAME}';")
            )
            exists = bool(result.all())
            if not exists:
                print("Create fulltext stoplist")
                db.execute(DDL(f"CREATE FULLTEXT STOPLIST {settings.MSSQL_SEARCH_STOPLIST_NAME};"))

            # Populate stoplist
            result = db.execute(
                text(
                    f"""
                    SELECT
                        stopword
                    FROM
                        sys.fulltext_stopwords w
                    LEFT JOIN
                        sys.fulltext_stoplists l
                            ON w.stoplist_id = l.stoplist_id WHERE name = '{settings.MSSQL_SEARCH_STOPLIST_NAME}'
                """
                )
            )
            words_in_stoplist = set([r[0] for r in result.all()])

            # Add new words to stoplist
            words_to_add: Set[str] = set.difference(stopwords, words_in_stoplist)
            for word in words_to_add:
                db.execute(
                    DDL(f"ALTER FULLTEXT STOPLIST {settings.MSSQL_SEARCH_STOPLIST_NAME} ADD '{word}' LANGUAGE 1043;")
                )

            # Remove words that no longer exist
            words_to_remove: Set[str] = set.difference(words_in_stoplist, stopwords)
            for word in words_to_remove:
                db.execute(
                    DDL(f"ALTER FULLTEXT STOPLIST {settings.MSSQL_SEARCH_STOPLIST_NAME} DROP '{word}' LANGUAGE 1043;")
                )

            # Create the catalog
            result = db.execute(
                text(f"SELECT name FROM sys.fulltext_catalogs WHERE name = '{settings.MSSQL_SEARCH_FTC_NAME}';")
            )
            exists = bool(result.all())
            if not exists:
                print("Create fulltext catalog")
                db.execute(DDL(f"CREATE FULLTEXT CATALOG {settings.MSSQL_SEARCH_FTC_NAME};"))

            for search_config in main_config.get("mssql_search", []):
                table_name = search_config.get("table_name")
                columns = search_config.get("searchable_columns_low", []) + search_config.get(
                    "searchable_columns_high", []
                )
                _reset_fulltext_index(db, table_name, set(columns))

        click.echo("Done")

    return setup_search_database
