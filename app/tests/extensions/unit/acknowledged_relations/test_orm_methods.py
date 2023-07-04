from datetime import datetime
from uuid import UUID

from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelationSide


class TestAcknowledgedRelationsSide:
    def test_relation_with_sides(self):
        side_a = AcknowledgedRelationSide(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Acknowledged=datetime(2023, 2, 2, 3, 3, 3),
            Acknowledged_By_UUID=UUID("11111111-0000-0000-0000-000000000001"),
            Explanation="",
        )
        side_b = AcknowledgedRelationSide(
            Object_ID=2,
            Object_Type="beleidskeuze",
            Acknowledged=datetime(2023, 2, 3, 3, 3, 3),
            Acknowledged_By_UUID=UUID("11111111-0000-0000-0000-000000000001"),
            Explanation="",
        )

        ack_table: AcknowledgedRelationsTable = AcknowledgedRelationsTable(
            Requested_By_Code="beleidskeuze-1",
            Created_Date=datetime(2023, 2, 2, 3, 3, 3),
            Created_By_UUID=UUID("11111111-0000-0000-0000-000000000001"),
            Modified_Date=datetime(2023, 2, 3, 3, 3, 3),
            Modified_By_UUID=UUID("11111111-0000-0000-0000-000000000001"),
        )
        ack_table.with_sides(side_a, side_b)

        assert ack_table.From_Code == side_a.Code
        assert ack_table.To_Code == side_b.Code
        assert ack_table.Is_Acknowledged is True

    def test_relation_edit_side(self):
        side_a = AcknowledgedRelationSide(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Acknowledged=datetime(2023, 2, 2, 3, 3, 3),
            Acknowledged_By_UUID=UUID("11111111-0000-0000-0000-000000000001"),
            Explanation="Relatie naar beleidskeuze 2",
        )
        side_b = AcknowledgedRelationSide(
            Object_ID=2,
            Object_Type="beleidskeuze",
            Acknowledged=datetime(2023, 2, 3, 3, 3, 3),
            Acknowledged_By_UUID=UUID("11111111-0000-0000-0000-000000000001"),
            Explanation="Relatie naar beleidskeuze 1",
        )

        ack_table: AcknowledgedRelationsTable = AcknowledgedRelationsTable(
            Requested_By_Code="beleidskeuze-1",
            Created_Date=datetime(2023, 2, 2, 3, 3, 3),
            Created_By_UUID=UUID("11111111-0000-0000-0000-000000000001"),
            Modified_Date=datetime(2023, 2, 3, 3, 3, 3),
            Modified_By_UUID=UUID("11111111-0000-0000-0000-000000000001"),
        )
        ack_table.with_sides(side_a, side_b)

        assert ack_table.From_Explanation == "Relatie naar beleidskeuze 2"
        assert ack_table.To_Explanation == "Relatie naar beleidskeuze 1"
        test_side = ack_table.get_side("beleidskeuze-1")
        assert test_side.Code == "beleidskeuze-1"

        test_side.Explanation = "New title"
        ack_table.apply_side(side=test_side)

        assert ack_table.From_Explanation == "New title"
