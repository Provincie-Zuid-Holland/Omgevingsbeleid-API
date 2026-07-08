from datetime import datetime, timezone

from app.api.domains.modules.types import ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules.module_beleidsdoel_spec import ModuleBeleidsdoelSpec
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_Date=datetime(2025, 6, 1, tzinfo=timezone.utc),
        Modified_Date=datetime(2025, 6, 1, tzinfo=timezone.utc),
        Created_By_UUID=col.ref(UserSpec, "admin"),
        Modified_By_UUID=col.ref(UserSpec, "admin"),
        Module_Manager_1_UUID=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_1",
                Module_ID=1,
                Title="Title of Module 1",
                Description="Description of Module 1",
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
                        Object_ID=1,
                    )
                ]
            )

            col.move_at(hours=1)
            col.adds(
                [
                    # Change record already in the module
                    ModuleBeleidsdoelSpec(
                        key="mod_1_beleidsdoel_1_second_entry",
                        Object_ID=1,
                        Title="Changed the titel via Module 1",
                    ),
                    # An new record
                    ModuleBeleidsdoelSpec(
                        key="mod_1_beleidsdoel_4_first_entry",
                        Object_ID=4,
                        Title="Beleidsdoel 4 from module 1",
                        Description="Description of beleidsdoel 4",
                    ),
                ]
            )

            # Pin the changes with a status change
            col.move_at(hours=1)
            col.add(
                ModuleStatusHistorySpec(
                    Status=ModuleStatusCode.Ontwerp_GS_Concept,
                )
            )

            col.move_at(hours=1)
            col.adds(
                [
                    # Change record already in the module
                    # But there is no status update after yet
                    ModuleBeleidsdoelSpec(
                        key="mod_1_beleidsdoel_1_third_entry",
                        Object_ID=1,
                        Title="Changed the titel via Module 1 again!",
                    ),
                ]
            )
