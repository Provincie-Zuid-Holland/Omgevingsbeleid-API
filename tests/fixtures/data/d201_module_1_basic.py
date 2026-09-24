from datetime import UTC, datetime

from app.api.domains.modules.types import ModuleStatusCode, ModuleStatusCodeInternal, PublicModuleStatusCode
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules.module_beleidsdoel_spec import ModuleBeleidsdoelSpec
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        created_date=datetime(2025, 6, 1, tzinfo=UTC),
        modified_date=datetime(2025, 6, 1, tzinfo=UTC),
        created_by_id=col.ref(UserSpec, "admin"),
        modified_by_id=col.ref(UserSpec, "admin"),
        module_manager_1_id=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_1",
                module_id=1,
                title="Title of Module 1",
                description="Description of Module 1",
            )
        )

        with col.in_module(1):
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
                    # An record to edit
                    ModuleBeleidsdoelSpec(
                        key="mod_1_beleidsdoel_1_first_entry",
                        object_id=1,
                    )
                ]
            )

            col.move_at(hours=1)
            col.adds(
                [
                    # Change record already in the module
                    ModuleBeleidsdoelSpec(
                        key="mod_1_beleidsdoel_1_second_entry",
                        object_id=1,
                        title="Changed the titel via Module 1",
                    ),
                    # An new record
                    ModuleBeleidsdoelSpec(
                        key="mod_1_beleidsdoel_4_first_entry",
                        object_id=4,
                        title="Beleidsdoel 4 from module 1",
                        description="Description of beleidsdoel 4",
                    ),
                ]
            )

            # We make it a public status now which will have effect on the /search endpoint for example
            col.move_at(hours=1)
            col.add(
                ModuleStatusHistorySpec(
                    Status=PublicModuleStatusCode.Ter_Inzage,
                )
            )

            col.move_at(hours=1)
            col.adds(
                [
                    # Change record already in the module
                    # But there is no status update after yet
                    ModuleBeleidsdoelSpec(
                        key="mod_1_beleidsdoel_1_third_entry",
                        object_id=1,
                        title="Changed the titel via Module 1 again!",
                    ),
                    # An record to edit
                    ModuleBeleidsdoelSpec(
                        key="mod_1_beleidsdoel_2_first_entry",
                        object_id=2,
                    ),
                ]
            )
