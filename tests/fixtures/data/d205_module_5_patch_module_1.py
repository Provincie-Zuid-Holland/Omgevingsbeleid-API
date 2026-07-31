from datetime import datetime, timezone

from app.api.domains.modules.types import ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules import (
    ModuleSpec,
    ModuleGebiedengroepSpec,
    ModuleGebiedSpec,
    ModuleGebiedsaanwijzingSpec,
)
from tests.fixtures.internal.spec.modules import ModuleStatusHistorySpec, ModuleBeleidskeuzeSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_Date=datetime(2025, 6, 5, tzinfo=timezone.utc),
        Modified_Date=datetime(2025, 6, 5, tzinfo=timezone.utc),
        Created_By_UUID=col.ref(UserSpec, "admin"),
        Modified_By_UUID=col.ref(UserSpec, "admin"),
        Module_Manager_1_UUID=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_5",
                Module_ID=5,
                Title="Title of Module 5",
                Description="Description of Module 5",
            )
        )

        with col.in_module(5):
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
                        key="mod_5_gebiedengroep_510", Object_ID=510, Title="Gebiedengroep 510 in Module 5"
                    ),
                    ModuleGebiedSpec(key="mod_5_gebied_510", Object_ID=510, Title="Gebied 510 in Module 5"),
                    ModuleGebiedsaanwijzingSpec(
                        key="mod_5_gebiedsaanwijzing_510", Object_ID=510, Title="Gebiedsaanwijzing 510 in Module 5"
                    ),
                ]
            )

            col.adds(
                [
                    # Edit of the live beleidskeuze-1
                    ModuleBeleidskeuzeSpec(
                        key="mod_5_beleidskeuze_1_first_entry",
                        Object_ID=1,
                    ),
                    # New beleidskeuze, so it has no live version yet
                    ModuleBeleidskeuzeSpec(
                        key="mod_5_beleidskeuze_510_first_entry",
                        Object_ID=510,
                        Title="Beleidskeuze 510 from module 5",
                        Description="Description of beleidskeuze 510",
                        Explanation="Explanation of beleidskeuze 510",
                        Owner_1_UUID=col.ref(UserSpec, "owner-1"),
                    ),
                ]
            )
