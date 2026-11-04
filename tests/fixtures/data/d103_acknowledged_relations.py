from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.acknowledged_relation_spec import AcknowledgedRelationSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    acknowledged_at = datetime(2025, 2, 1, tzinfo=UTC)

    col.adds(
        [
            AcknowledgedRelationSpec(
                key="beleidskeuze_1_beleidskeuze_2_pending",
                requested_by_code="beleidskeuze-1",
                from_code="beleidskeuze-1",
                from_acknowledged=acknowledged_at,
                from_acknowledged_by_id=col.ref(UserSpec, "admin"),
                from_explanation="Explanation from beleidskeuze 1",
                to_code="beleidskeuze-2",
            ),
            AcknowledgedRelationSpec(
                key="beleidskeuze_3_beleidskeuze_4_acknowledged",
                requested_by_code="beleidskeuze-3",
                from_code="beleidskeuze-3",
                from_acknowledged=acknowledged_at,
                from_acknowledged_by_id=col.ref(UserSpec, "admin"),
                from_explanation="Explanation from beleidskeuze 3",
                to_code="beleidskeuze-4",
                to_acknowledged=acknowledged_at,
                to_acknowledged_by_id=col.ref(UserSpec, "admin"),
                to_explanation="Explanation from beleidskeuze 4",
            ),
            AcknowledgedRelationSpec(
                key="beleidskeuze_1_beleidskeuze_3_denied",
                requested_by_code="beleidskeuze-1",
                from_code="beleidskeuze-1",
                from_acknowledged=acknowledged_at,
                from_acknowledged_by_id=col.ref(UserSpec, "admin"),
                to_code="beleidskeuze-3",
                denied=acknowledged_at,
            ),
            AcknowledgedRelationSpec(
                key="beleidskeuze_1_beleidskeuze_4_deleted",
                requested_by_code="beleidskeuze-1",
                from_code="beleidskeuze-1",
                to_code="beleidskeuze-4",
                deleted_at=acknowledged_at,
            ),
        ]
    )
