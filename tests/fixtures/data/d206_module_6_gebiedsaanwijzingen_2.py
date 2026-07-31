from datetime import datetime, timezone

from app.api.domains.modules.types import ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules import (
    ModuleSpec,
    ModuleGebiedengroepSpec,
    ModuleGebiedSpec,
    ModuleGebiedsaanwijzingSpec,
)
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
                key="module_6",
                Module_ID=6,
                Title="Title of Module 6",
                Description="Description of Module 6",
            )
        )

        with col.in_module(6):
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
                    # Created Gebiedengroepen and Gebieden
                    # Which should not be usable by other modules yet
                    ModuleGebiedengroepSpec(
                        key="mod_6_gebiedengroep_610", Object_ID=610, Title="Gebiedengroep 610 in Module 6"
                    ),
                    ModuleGebiedSpec(key="mod_6_gebied_610", Object_ID=610, Title="Gebied 610 in Module 6"),
                    ModuleGebiedsaanwijzingSpec(
                        key="mod_6_gebiedsaanwijzing_610", Object_ID=610, Title="Gebiedsaanwijzing 610 in Module 6"
                    ),
                ]
            )
