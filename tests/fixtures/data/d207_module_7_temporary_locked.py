from datetime import UTC, datetime

from app.api.domains.modules.types import ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules import ModuleBeleidsdoelSpec
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        created_date=datetime(2025, 6, 7, tzinfo=UTC),
        modified_date=datetime(2025, 6, 7, tzinfo=UTC),
        created_by_id=col.ref(UserSpec, "admin"),
        modified_by_id=col.ref(UserSpec, "admin"),
        module_manager_1_id=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_7",
                module_id=7,
                title="Title of Module 7",
                description="Description of Module 7",
                temporary_locked=True,
            )
        )
        with col.in_module(7):
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
            col.adds(
                [
                    # A record, but is invalid because of missing title
                    ModuleBeleidsdoelSpec(
                        key="mod_7_beleidsdoel_7_first_entry",
                        object_id=7,
                    )
                ]
            )
