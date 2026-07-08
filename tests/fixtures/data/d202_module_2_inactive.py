from datetime import datetime, timezone

from app.api.domains.modules.types import ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_Date=datetime(2025, 6, 2, tzinfo=timezone.utc),
        Modified_Date=datetime(2025, 6, 2, tzinfo=timezone.utc),
        Created_By_UUID=col.ref(UserSpec, "admin"),
        Modified_By_UUID=col.ref(UserSpec, "admin"),
        Module_Manager_1_UUID=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_2",
                Module_ID=2,
                Title="Title of Module 2",
                Description="Description of Module 2",
                Activated=False,
            )
        )
        with col.in_module(2):
            col.add(
                ModuleStatusHistorySpec(
                    Status=ModuleStatusCodeInternal.Niet_Actief,
                )
            )
