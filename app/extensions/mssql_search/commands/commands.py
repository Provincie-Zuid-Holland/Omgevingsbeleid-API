from typing import Set

import click
from sqlalchemy import DDL, text
from sqlalchemy.orm import Session

from app.core.db.session import SessionLocalWithAutoCommit
from app.core.settings import settings
from app.extensions.mssql_search.config.stopwords import stopwords


def _reset_fulltext_index(db: Session, table_name: str):
    # Check is this table already has a search index set up
    result = db.execute(
        text(
            f"SELECT * FROM sys.fulltext_indexes WHERE object_id = object_id('{table_name}');"
        )
    )
    exists = bool(result.all())
    if exists:
        db.execute(DDL(f"DROP FULLTEXT INDEX ON {table_name}"))

    # ft_index_exists = list(
    #     cur.execute(
    #         f"SELECT * FROM sys.fulltext_indexes WHERE object_id = object_id('{self.schema.Meta.table}')"
    #     )
    # )

    # if ft_index_exists:
    #     cur.execute(f"DROP FULLTEXT INDEX ON {self.schema.Meta.table}")

    # # Set up new search
    # search_title_fields = self.schema.fields_with_props(["search_title"])
    # search_description_fields = self.schema.fields_with_props(
    #     ["search_description"]
    # )

    # search_fields = []

    # if search_title_fields:
    #     assert (
    #         len(search_title_fields) == 1
    #     ), f"More then one search_title field defined on object {self.schema.Meta.slug}"

    #     search_fields.append(f"{search_title_fields[0]} Language 1043")

    # if search_description_fields:

    #     search_description_fields = map(
    #         lambda f: f"{f} Language 1043", search_description_fields
    #     )
    #     search_fields += search_description_fields

    # if search_fields:
    #     cur.execute(
    #         f"""CREATE FULLTEXT INDEX ON {self.schema.Meta.table} (
    #                         {', '.join(search_fields)}
    #                     )
    #                     KEY INDEX PK_{self.schema.Meta.table}
    #                     ON {ftc_name}
    #                     WITH CHANGE_TRACKING = AUTO, STOPLIST = {stoplist_name}
    #         """
    #     )


@click.command()
def setup_search_database():
    click.echo("Initialized search tables")

    with SessionLocalWithAutoCommit() as db:
        # Create stoplist
        result = db.execute(
            text(
                f"SELECT name FROM sys.fulltext_stoplists WHERE name = '{settings.MSSQL_SEARCH_STOPLIST_NAME}';"
            )
        )
        exists = bool(result.all())
        if not exists:
            print("Create fulltext stoplist")
            db.execute(
                DDL(f"CREATE FULLTEXT STOPLIST {settings.MSSQL_SEARCH_STOPLIST_NAME};")
            )

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
                DDL(
                    f"ALTER FULLTEXT STOPLIST {settings.MSSQL_SEARCH_STOPLIST_NAME} ADD '{word}' LANGUAGE 1043;"
                )
            )

        # Remove words that no longer exist
        words_to_remove: Set[str] = set.difference(words_in_stoplist, stopwords)
        for word in words_to_remove:
            db.execute(
                DDL(
                    f"ALTER FULLTEXT STOPLIST {settings.MSSQL_SEARCH_STOPLIST_NAME} DROP '{word}' LANGUAGE 1043;"
                )
            )

        # Create the catalog
        result = db.execute(
            text(
                f"SELECT name FROM sys.fulltext_catalogs WHERE name = '{settings.MSSQL_SEARCH_FTC_NAME}';"
            )
        )
        exists = bool(result.all())
        if not exists:
            print("Create fulltext catalog")
            db.execute(
                DDL(f"CREATE FULLTEXT CATALOG {settings.MSSQL_SEARCH_FTC_NAME};")
            )

        # @todo: these should be defined in the main config. Together with the field names
        """
        mssql_search:
            - objects
                high_rank_fields:
                    - Titel
                low_rank_fields:
                    - Description
        """
        _reset_fulltext_index(db, "objects")
        # _reset_fulltext_index(db, "module_objects")

    click.echo("Done")
