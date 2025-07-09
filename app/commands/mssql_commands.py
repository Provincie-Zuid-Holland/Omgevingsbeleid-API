from typing import Annotated, Set

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy import DDL, inspect, text
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.core.services.main_config import MainConfig

stopwords: Set[str] = set(
    [
        "de",
        "en",
        "van",
        "ik",
        "te",
        "dat",
        "die",
        "in",
        "een",
        "hij",
        "het",
        "niet",
        "zijn",
        "is",
        "was",
        "op",
        "aan",
        "met",
        "als",
        "voor",
        "had",
        "er",
        "maar",
        "om",
        "hem",
        "dan",
        "zou",
        "of",
        "wat",
        "mijn",
        "men",
        "dit",
        "zo",
        "door",
        "over",
        "ze",
        "zich",
        "bij",
        "ook",
        "tot",
        "je",
        "mij",
        "uit",
        "der",
        "daar",
        "haar",
        "naar",
        "heb",
        "hoe",
        "heeft",
        "hebben",
        "deze",
        "u",
        "want",
        "nog",
        "zal",
        "me",
        "zij",
        "nu",
        "ge",
        "geen",
        "omdat",
        "iets",
        "worden",
        "toch",
        "al",
        "waren",
        "veel",
        "meer",
        "doen",
        "toen",
        "moet",
        "ben",
        "zonder",
        "kan",
        "hun",
        "dus",
        "alles",
        "onder",
        "ja",
        "eens",
        "hier",
        "wie",
        "werd",
        "altijd",
        "doch",
        "wordt",
        "wezen",
        "kunnen",
        "ons",
        "zelf",
        "tegen",
        "na",
        "reeds",
        "wil",
        "kon",
        "niets",
        "uw",
        "iemand",
        "geweest",
        "andere",
        "zuid",
        "holland",
        "zuid-holland",
    ]
)


def _reset_fulltext_index(
    db: Session,
    mssql_search_ftc_name: str,
    mssql_search_stoplist_name: str,
    table_name: str,
    columns: Set[str],
):
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
        ON {mssql_search_ftc_name}
        WITH CHANGE_TRACKING = AUTO, STOPLIST = {mssql_search_stoplist_name}
    """
    db.execute(text(query))


@click.command()
@inject
def mssql_setup_search_database(
    db: Annotated[Session, Provide[ApiContainer.db]],
    mssql_search_ftc_name: Annotated[str, Provide[ApiContainer.config.MSSQL_SEARCH_FTC_NAME]],
    mssql_search_stoplist_name: Annotated[str, Provide[ApiContainer.config.MSSQL_SEARCH_STOPLIST_NAME]],
    main_config: Annotated[MainConfig, Provide[ApiContainer.main_config]],
):
    click.echo("Initialized search tables")
    click.echo(mssql_search_stoplist_name)

    # Create stoplist
    result = db.execute(text(f"SELECT name FROM sys.fulltext_stoplists WHERE name = '{mssql_search_stoplist_name}';"))
    exists = bool(result.all())
    if not exists:
        print("Create fulltext stoplist")
        db.execute(DDL(f"CREATE FULLTEXT STOPLIST {mssql_search_stoplist_name};"))

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
                    ON w.stoplist_id = l.stoplist_id WHERE name = '{mssql_search_stoplist_name}'
        """
        )
    )
    words_in_stoplist = set([r[0] for r in result.all()])

    # Add new words to stoplist
    words_to_add: Set[str] = set.difference(stopwords, words_in_stoplist)
    for word in words_to_add:
        db.execute(DDL(f"ALTER FULLTEXT STOPLIST {mssql_search_stoplist_name} ADD '{word}' LANGUAGE 1043;"))

    # Remove words that no longer exist
    words_to_remove: Set[str] = set.difference(words_in_stoplist, stopwords)
    for word in words_to_remove:
        db.execute(DDL(f"ALTER FULLTEXT STOPLIST {mssql_search_stoplist_name} DROP '{word}' LANGUAGE 1043;"))

    # Create the catalog
    result = db.execute(text(f"SELECT name FROM sys.fulltext_catalogs WHERE name = '{mssql_search_ftc_name}';"))
    exists = bool(result.all())
    if not exists:
        print("Create fulltext catalog")
        db.execute(DDL(f"CREATE FULLTEXT CATALOG {mssql_search_ftc_name};"))

    main_config_dict: dict = main_config.get_main_config()
    for search_config in main_config_dict.get("mssql_search", []):
        table_name = search_config.get("table_name")
        columns = search_config.get("searchable_columns_low", []) + search_config.get("searchable_columns_high", [])
        _reset_fulltext_index(
            db,
            mssql_search_ftc_name,
            mssql_search_stoplist_name,
            table_name,
            set(columns),
        )

    click.echo("Done")
