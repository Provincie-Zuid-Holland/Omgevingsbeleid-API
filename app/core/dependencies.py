from contextlib import contextmanager
from typing import Generator

from app.core.db.session import SessionLocal


def depends_db() -> Generator:
    db = SessionLocal()
    try:
        # @todo: should be checking database type first
        # db.execute(text("pragma foreign_keys=on"))
        yield db
    except Exception as e:
        # Gives me a place to inspect
        raise e
    finally:
        db.close()


@contextmanager
def db_in_context_manager() -> Generator:
    yield from depends_db()
