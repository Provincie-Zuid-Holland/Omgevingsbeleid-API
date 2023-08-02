from datetime import datetime
from uuid import UUID

from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelationSide

from .fixtures import local_tables  # noqa


class TestModelIntegration:
    def test_relation_with_sides(self, local_tables, db):  # noqa
        my_user = UUID("11111111-0000-0000-0000-000000000001")
        my_side = AcknowledgedRelationSide(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Acknowledged=datetime.utcnow(),
            Acknowledged_By_UUID=my_user,
            Explanation="Relatie naar beleidskeuze 1",
        )
        their_side = AcknowledgedRelationSide(
            Object_ID=2,
            Object_Type="beleidskeuze",
        )

        ack_table: AcknowledgedRelationsTable = local_tables.AcknowledgedRelationsTable(
            Requested_By_Code=my_side.Code,
            Created_Date=datetime.utcnow(),
            Created_By_UUID=my_user,
            Modified_Date=datetime.utcnow(),
            Modified_By_UUID=my_user,
        )
        ack_table.with_sides(my_side, their_side)

        db.add(ack_table)
        db.flush()
        db.commit()
