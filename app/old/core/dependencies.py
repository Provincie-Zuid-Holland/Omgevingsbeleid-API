from contextlib import contextmanager
from typing import Generator

import yaml
from fastapi import Depends, Request
from sqlalchemy import text

from app.core_old.db.session import SessionLocal
from app.core_old.security import Security
from app.core_old.settings.dynamic_settings import DynamicSettings


def depends_db() -> Generator:
    with SessionLocal() as db:
        try:
            if db.bind.dialect.name == "sqlite":
                db.execute(text("pragma foreign_keys=on"))
                db.execute(text("SELECT load_extension('mod_spatialite')"))
            yield db
        except Exception as e:
            # Gives me a place to inspect
            raise e


@contextmanager
def db_in_context_manager() -> Generator:
    yield from depends_db()


def depends_settings(request: Request) -> DynamicSettings:
    return request.app.state.settings


def depends_main_config(settings: DynamicSettings = Depends(depends_settings)) -> dict:
    with open(settings.MAIN_CONFIG_FILE) as stream:
        return yaml.safe_load(stream)


def depends_security(settings: DynamicSettings = Depends(depends_settings)) -> Security:
    return Security(settings)
