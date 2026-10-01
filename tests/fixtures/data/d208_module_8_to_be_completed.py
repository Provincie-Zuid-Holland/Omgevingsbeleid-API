from datetime import UTC, datetime

from app.api.domains.modules.types import ModuleObjectActionFull, ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules import ModuleBeleidsdoelSpec, ModuleBeleidskeuzeSpec
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        created_date=datetime(2025, 7, 1, tzinfo=UTC),
        modified_date=datetime(2025, 7, 1, tzinfo=UTC),
        created_by_id=col.ref(UserSpec, "admin"),
        modified_by_id=col.ref(UserSpec, "admin"),
        module_manager_1_id=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_8",
                module_id=8,
                title="Title of Module 8",
                description="Description of Module 8",
                temporary_locked=True,
            )
        )
        with col.in_module(8):
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
                    Status=ModuleStatusCode.Vastgesteld,
                )
            )

            col.move_at(hours=1)
            col.adds(
                [
                    ModuleBeleidsdoelSpec(
                        key="mod_8_beleidsdoel_8",
                        object_id=8,
                        title="Beleidsdoel 8",
                        description="Description of beleidsdoel 8",
                    )
                ]
            )
            col.move_at(hours=1)
            col.adds(
                [
                    ModuleBeleidskeuzeSpec(
                        key="mod_8_beleidskeuze_8",
                        object_id=8,
                        title="Beleidskeuze 8",
                        description="Description of beleidskeuze 8",
                    )
                ]
            )
            col.move_at(hours=1)
            col.adds(
                [
                    ModuleBeleidskeuzeSpec(
                        key="mod_8_beleidskeuze_9",
                        object_id=9,
                        title="Beleidskeuze 9 (to be terminated)",
                        description="Description of beleidskeuze 9",
                        context_action=ModuleObjectActionFull.Terminate,
                    )
                ]
            )
