from datetime import datetime, timezone

from app.api.domains.modules.types import ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_Date=datetime(2025, 6, 4, tzinfo=timezone.utc),
        Modified_Date=datetime(2025, 6, 4, tzinfo=timezone.utc),
        Created_By_UUID=col.ref(UserSpec, "admin"),
        Modified_By_UUID=col.ref(UserSpec, "admin"),
        # Managed by the ambtenaar, whose role lacks module_can_close_module:
        # the close permission must come from the manager whitelist, not the role.
        Module_Manager_1_UUID=col.ref(UserSpec, "ambtenaar"),
    ):
        col.add(
            ModuleSpec(
                key="module_4",
                Module_ID=4,
                Title="Title of Module 4",
                Description="Description of Module 4",
            )
        )
        with col.in_module(4):
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
