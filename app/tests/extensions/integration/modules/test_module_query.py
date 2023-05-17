from uuid import UUID
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session, aliased
from sqlalchemy.orm.session import make_transient

from app.dynamic.dependencies import FilterObjectCode
from app.extensions.modules.repository import (
    ModuleRepository,
    ModuleObjectRepository
)
from app.tests.fixture_factories import (
    ModuleFixtureFactory,
    UserFixtureFactory,
    ObjectFixtureFactory,
    ObjectStaticsFixtureFactory
)
from app.tests.helpers import patch_multiple

from .fixtures import (
    ExtendedLocalTables,
    local_tables,  # noqa
    module_context_repo,
    module_object_repo,
    module_repo,
    setup_db,
)

class TestModuleQuery:
    @pytest.fixture(autouse=True)
    def setup(self, db, local_tables, setup_db):  # noqa
        # timestamps
        self.now = datetime.now()
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)

        # Factory data
        self.user_factory = UserFixtureFactory(db)
        self.user_factory.populate_db()

        self.super_user = self.user_factory.objects[0]
        self.ba_user = self.user_factory.objects[2]
        self.pf_user = self.user_factory.objects[4]

        mf = ModuleFixtureFactory(db, local_tables)
        mf.create_all_modules()
        mf.create_all_module_status_history()
        mf.create_all_module_object_context()
        mf.create_all_module_objects()
        mf.populate_db()
        self.module_factory = mf

        osf = ObjectStaticsFixtureFactory(db, local_tables)
        osf.populate_db()

        of = ObjectFixtureFactory(db, local_tables)
        of.populate_db()

    def test_module_get_all_objects(
        self, db: Session, local_tables: ExtendedLocalTables,
    ):
        lt = local_tables
        # Input User UUID
        # Filteren op Owner + Object_Type
        owner = UUID("11111111000000000000000000000001")

        stmt = (
            select(lt.ObjectsTable)
            .where(lt.ObjectStaticsTable.Owner_1_UUID == owner)
            .order_by(desc(lt.ObjectsTable.Modified_Date))
        )
        result = db.scalars(stmt).all()

        # stmt = (
        #     select(ObjectsTable)
        #     .select_from(ObjectsTable)
        #     .outerjoin(ObjectStaticsTable, ObjectsTable.Code == ObjectStaticsTable.Code)
        #     .where(or_(ObjectStaticsTable.Owner_1_UUID == owner, ObjectStaticsTable.Owner_1_UUID == None))
        #     .order_by(desc(ObjectsTable.Modified_Date))
        # )

        # [
        #   {
        #       "static": { ObjectStatics },
        #       "vigerend": { nieuwst-vigerende-object },
        #       "modules": [{ ModuleA.niewueste-aanpassing }, { ModuleB.niewueste-aanpassing }] # Nieuwste versie van  object in module (zolang module niet gesloten is)
        #   }
        # ]

        print(len(result))
        for ob in result:
            print(f"{ob.Code} - {ob.UUID}")

