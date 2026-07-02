from datetime import datetime, timezone

from app.api.domains.modules.types import ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_Date=datetime(2025, 6, 3, tzinfo=timezone.utc),
        Modified_Date=datetime(2025, 6, 3, tzinfo=timezone.utc),
        Created_By_UUID=col.ref(UserSpec, "admin"),
        Modified_By_UUID=col.ref(UserSpec, "admin"),
        Module_Manager_1_UUID=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_3",
                Module_ID=3,
                Title="Title of Module 3",
                Description="Description of Module 3",
                Closed=True,
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
