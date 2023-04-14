import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extensions.acknowledged_relations.endpoints.request_acknowledged_relation import (
    EndpointHandler as RequestEndpoint,
)
from app.extensions.acknowledged_relations.endpoints.request_acknowledged_relation import (
    RequestAcknowledgedRelation,
)
from .fixtures import local_tables, ExtendedLocalTables  # noqa


class TestAcknowledgedRelationsEndpoint:
    """
    Test handling the endpoint and building AcknowledgedRelation models
    """

    @pytest.fixture
    def populate_db(self, local_tables: ExtendedLocalTables, db: Session):
        self.now = datetime.now()
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)
        self.user_1 = local_tables.UsersTabel(
            UUID=uuid.uuid4(),
            Gebruikersnaam="monty",
            Email="monty@pzh.nl",
            Wachtwoord="monty",
        )
        self.user_2 = local_tables.UsersTabel(
            UUID=uuid.uuid4(),
            Gebruikersnaam="python",
            Email="python@pzh.nl",
            Wachtwoord="monty",
        )
        self.statics = [
            local_tables.ObjectStaticsTable(
                Object_Type="beleidskeuze", Object_ID=1, Code="beleidskeuze-1"
            ),
            local_tables.ObjectStaticsTable(
                Object_Type="beleidskeuze", Object_ID=2, Code="beleidskeuze-2"
            ),
            local_tables.ObjectStaticsTable(
                Object_Type="beleidskeuze", Object_ID=3, Code="beleidskeuze-3"
            ),
        ]
        self.objects = [
            local_tables.ObjectsTable(
                UUID=uuid.uuid4(),
                Modified_Date=self.now,
                Code="beleidskeuze-1",
                Object_ID=1,
                Object_Type="beleidskeuze",
                Start_Validity=self.five_days_ago,
                End_Validity=self.five_days_later,
            ),
            local_tables.ObjectsTable(
                UUID=uuid.uuid4(),
                Modified_Date=self.now,
                Code="beleidskeuze-2",
                Object_ID=2,
                Object_Type="beleidskeuze",
                Start_Validity=self.five_days_ago,
                End_Validity=self.five_days_later,
            ),
            local_tables.ObjectsTable(
                UUID=uuid.uuid4(),
                Modified_Date=self.now,
                Code="beleidskeuze-3",
                Object_ID=3,
                Object_Type="beleidskeuze",
                Start_Validity=self.five_days_ago,
                End_Validity=self.five_days_later,
            ),
        ]
        try:
            db.add_all(self.statics)
            db.add_all(self.objects)
            db.commit()
            yield
        except Exception:
            raise Exception("Invalid fixture data")

    def test_request_endpoint_initial_state(
        self, db: Session, local_tables: ExtendedLocalTables, populate_db
    ):
        request_obj = RequestAcknowledgedRelation(
            ID=2, Object_Type="beleidskeuze", Title="monty", Explanation="python"
        )
        endpoint = RequestEndpoint(
            db=db,
            user=self.user_1,
            object_type="beleidskeuze",
            lineage_id=1,
            allowed_object_types=["beleidskeuze"],
            object_in=request_obj,
        )

        response = endpoint.handle()

        assert response.message == "OK"

        stmt = (
            select(local_tables.AcknowledgedRelationsTable)
            .filter(
                local_tables.AcknowledgedRelationsTable.Requested_By_Code
                == "beleidskeuze-1"
            )
            .filter(
                local_tables.AcknowledgedRelationsTable.From_Code == "beleidskeuze-1"
            )
            .filter(local_tables.AcknowledgedRelationsTable.To_Code == "beleidskeuze-2")
            .filter(local_tables.AcknowledgedRelationsTable.From_Title == "monty")
        )

        db_item = db.scalars(stmt).first()
        # assert From side is acknowledged, to side is empty
        assert db_item is not None
        assert db_item.From_Acknowledged == 1
        assert db_item.To_Acknowledged == 0
        assert db_item.To_Acknowledged_Date is None
        assert db_item.To_Acknowledged_By_UUID is None
        assert db_item.To_Title == ""
        assert db_item.To_Explanation == ""

    # def test_request_endpoint_acknowledged_state(
    #     self,
    #     db: Session,
    #     table_setup: LocalTables,
    # ):
    #     request_obj = RequestAcknowledgedRelation(
    #         ID=2, Object_Type="beleidskeuze", Title="monty", Explanation="python"
    #     )
    #     endpoint = RequestEndpoint(
    #         db=db,
    #         user=self.user_1,
    #         object_type="beleidskeuze",
    #         lineage_id=1,
    #         allowed_object_types=["beleidskeuze"],
    #         object_in=request_obj,
    #     )

    #     response = endpoint.handle()

    #     assert response.message == "OK"

    #     stmt = (
    #         select(table_setup.AcknowledgedRelationsTable)
    #         .filter(table_setup.AcknowledgedRelationsTable.Requested_By_Code == "beleidskeuze-1")
    #         .filter(table_setup.AcknowledgedRelationsTable.From_Code == "beleidskeuze-1")
    #         .filter(table_setup.AcknowledgedRelationsTable.To_Code == "beleidskeuze-2")
    #         .filter(table_setup.AcknowledgedRelationsTable.From_Title == "monty")
    #     )

    #     db_item = db.scalars(stmt).first()
    #     # assert From side is acknowledged, to side is empty
    #     assert db_item is not None
    #     assert db_item.From_Acknowledged == 1
    #     assert db_item.To_Acknowledged == 0
    #     assert db_item.To_Acknowledged_Date is None
    #     assert db_item.To_Acknowledged_By_UUID is None
    #     assert db_item.To_Title == ""
    #     assert db_item.To_Explanation == ""


# class TestAcknowledgedRelationsRepository:
#     """
#     Test query logic and from/to side mapping.
#     """

#     @pytest.fixture
#     def table_setup(db: Session, engine: Engine, local_tables: LocalTables):
#         # setup db
#         local_tables.Base.metadata.drop_all(engine)
#         local_tables.Base.metadata.create_all(engine)
#         yield local_tables
#         # teardown db
#         # local_tables.Base.metadata.drop_all(engine)

#     @pytest.fixture
#     def populate_db(self, table_setup, db: Session):
#         self.now = datetime.now()
#         self.five_days_ago = self.now - timedelta(days=5)
#         self.five_days_later = self.now + timedelta(days=5)
#         self.statics = [
#             table_setup.ObjectStaticsTable(
#                 Object_Type="ambitie", Object_ID=1, Code="ambitie-1"
#             ),
#             table_setup.ObjectStaticsTable(
#                 Object_Type="ambitie", Object_ID=2, Code="ambitie-2"
#             ),
#             table_setup.ObjectStaticsTable(
#                 Object_Type="beleidskeuze", Object_ID=1, Code="beleidskeuze-1"
#             ),
#         ]
#         try:
#             db.add_all(self.statics)
#             db.commit()
#             yield
#         except Exception:
#             raise Exception("Invalid fixture data")

#     @pytest.fixture
#     def repository(self, db):
#         return AcknowledgedRelationsRepository(db=db)

#     def test_get_by_codes(
#         self,
#         db: Session,
#         table_setup: LocalTables,
#         repository: AcknowledgedRelationsRepository,
#         populate_db,
#     ):
#         pass
