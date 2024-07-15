from contextlib import contextmanager
from typing import Generator

from sqlalchemy import text

from app.core.db.session import SessionLocal, ScopedSessionLocal


def depends_db() -> Generator:
    # db = SessionLocal()
    db = ScopedSessionLocal()
    try:
        if db.bind.dialect.name == "sqlite":
            db.execute(text("pragma foreign_keys=on"))
            db.execute(text("SELECT load_extension('mod_spatialite')"))
        yield db
    except Exception as e:
        # Gives me a place to inspect
        raise e
    finally:
        db.close()


@contextmanager
def db_in_context_manager() -> Generator:
    yield from depends_db()
