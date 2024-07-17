from contextlib import contextmanager
from typing import Generator

from fastapi import Request

# def depends_db() -> Generator:
#     with SessionLocal() as db:
#         try:
#             if db.bind.dialect.name == "sqlite":
#                 db.execute(text("pragma foreign_keys=on"))
#                 db.execute(text("SELECT load_extension('mod_spatialite')"))
#             yield db
#         except Exception as e:
#             # Gives me a place to inspect
#             raise e


def depends_db(request: Request):
    return request.state.db


@contextmanager
def db_in_context_manager() -> Generator:
    yield from depends_db()
