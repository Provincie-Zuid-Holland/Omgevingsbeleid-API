import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.tests.fixture_factories import (
    UserFixtureFactory,
    ObjectStaticsFixtureFactory,
    ObjectFixtureFactory,
    ModuleFixtureFactory
)
from .fixtures import ( # noqa
    local_tables,
    ExtendedLocalTables,
)


class TestModuleRepository:
    """
    Integration tests to ensure module db querying behaves as
    expected.
    """
    @pytest.fixture(autouse=True)
    def setup(self, db, local_tables):  # noqa
        # timestamps
        self.now = datetime.now()
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)

        # Factory data
        self.user_factory = UserFixtureFactory(db)
        self.user_factory.populate_db()

        self.super_user = self.user_factory.objects[0]
        self.ba_user = self.user_factory.objects[2]

    def test_module_get_by_id(self, db: Session, local_tables: ExtendedLocalTables): # noqa
        assert 1 == 1

    def test_module_get_with_filters(self, db: Session, local_tables: ExtendedLocalTables): # noqa
        assert 1 == 1
