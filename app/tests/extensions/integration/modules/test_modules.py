
from sqlalchemy.orm import Session

from .fixtures import (
    ExtendedLocalTables,
)


class TestModulesExtension:
    """
    Integration test endpoints to ensure DB querys
    and (de)serializing is working as expected.
    """

    def test_module_create(
        self,
        db: Session,
        local_tables: ExtendedLocalTables,
        mock_dispatcher,
        populate_users,
        populate_modules,
    ):
        # TODO: Fix module factory typing error on objects class first
        # Then finish tests

        assert 1 == 1
