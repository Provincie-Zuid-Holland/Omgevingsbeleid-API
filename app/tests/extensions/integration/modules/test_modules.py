import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from .fixtures import ExtendedLocalTables


class TestModulesExtension:
    """
    Integration test endpoints to ensure DB querys
    and (de)serializing is working as expected.
    """

    @pytest.fixture
    def populate_db(self, local_tables: ExtendedLocalTables, db: Session):
        self.now = datetime.now()
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)

        self.non_valid = local_tables.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-1",
            Modified_Date=self.now,
            Object_Type="ambitie",
            Object_ID=1,
            Start_Validity=self.five_days_later,
            End_Validity=None,
        )

        self.valid = local_tables.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-2",
            Modified_Date=self.five_days_ago,
            Object_Type="ambitie",
            Object_ID=2,
            Start_Validity=self.five_days_ago,
            End_Validity=self.five_days_later,
        )

        self.valid_latest = local_tables.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-2",
            Modified_Date=self.now,
            Object_Type="ambitie",
            Object_ID=2,
            Start_Validity=self.five_days_ago,
            End_Validity=self.five_days_later,
        )

        self.other_type = local_tables.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="beleidskeuze-1",
            Modified_Date=self.now,
            Object_Type="beleidskeuze",
            Object_ID=1,
            Start_Validity=self.five_days_ago,
            End_Validity=None,
        )

        self.statics = [
            local_tables.ObjectStaticsTable(
                Object_Type="ambitie", Object_ID=1, Code="ambitie-1"
            ),
            local_tables.ObjectStaticsTable(
                Object_Type="ambitie", Object_ID=2, Code="ambitie-2"
            ),
            local_tables.ObjectStaticsTable(
                Object_Type="beleidskeuze", Object_ID=1, Code="beleidskeuze-1"
            ),
        ]
        try:
            db.add_all(self.statics)
            db.add_all([self.non_valid, self.valid, self.valid_latest, self.other_type])
            db.commit()
            yield
        except Exception:
            raise Exception("Invalid fixture data")

    def test_module_create(
        self,
        db: Session,
        local_tables: ExtendedLocalTables,
        mock_dispatcher,
        populate_db,
    ):
        # Setup endpoint
        assert 1 == 1
