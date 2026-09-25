from datetime import UTC, datetime

from app.api.domains.modules.types import ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        created_date=datetime(2025, 6, 3, tzinfo=UTC),
        modified_date=datetime(2025, 6, 3, tzinfo=UTC),
        created_by_id=col.ref(UserSpec, "admin"),
        modified_by_id=col.ref(UserSpec, "admin"),
        module_manager_1_id=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_3",
                module_id=3,
                title="Title of Module 3",
                description="Description of Module 3",
                closed=True,
            )
        )
        with col.in_module(3):
            col.add(
                ModuleStatusHistorySpec(
                    Status=ModuleStatusCodeInternal.Niet_Actief,
                )
            )
            col.move_at(hours=1)
            col.add(
                ModuleStatusHistorySpec(
                    Status=ModuleStatusCode.Ontwerp_GS_Concept,
                )
            )
            col.move_at(hours=1)
            col.add(
                ModuleStatusHistorySpec(
                    Status=ModuleStatusCodeInternal.Gesloten,
                )
            )
