from typing import Generator

from sqlalchemy import text


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
