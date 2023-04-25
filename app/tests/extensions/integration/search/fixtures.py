import pytest

from sqlalchemy.orm import Session

# from app.tests.fixtures import LocalTables, LocalTableFactory
from app.tests.fixture_factories import (
    UserFixtureFactory,
    ObjectStaticsFixtureFactory,
)


# Extend to add tables for acknowledged relation module
# @pytest.fixture
# def local_tables(db: Session, engine: Engine):
#     factory = ExtendedTableFactory()
#     local_tables = factory.local_tables

#     # setup db
#     local_tables.Base.metadata.drop_all(engine)
#     local_tables.Base.metadata.create_all(engine)

#     yield local_tables
#     # teardown db
#     local_tables.Base.metadata.drop_all(engine)


@pytest.fixture
def populate_users(db: Session):
    uf = UserFixtureFactory(db)
    uf.create_all_objects()
    uf.populate_db()
    yield uf.objects


@pytest.fixture
def populate_statics(db: Session):
    uf = ObjectStaticsFixtureFactory(db)
    uf.create_all_objects()
    uf.populate_db()
    yield uf.objects
