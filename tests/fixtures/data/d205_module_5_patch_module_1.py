from datetime import UTC, datetime

from app.api.domains.modules.types import ModuleObjectActionFull, ModuleStatusCode, ModuleStatusCodeInternal
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules import (
    ModuleBeleidskeuzeSpec,
    ModuleGebiedengroepSpec,
    ModuleGebiedsaanwijzingSpec,
    ModuleGebiedSpec,
    ModuleSpec,
    ModuleStatusHistorySpec,
)
from tests.fixtures.internal.spec.modules.module_maatregel_spec import ModuleMaatregelSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        created_date=datetime(2025, 6, 5, tzinfo=UTC),
        modified_date=datetime(2025, 6, 5, tzinfo=UTC),
        created_by_id=col.ref(UserSpec, "admin"),
        modified_by_id=col.ref(UserSpec, "admin"),
        module_manager_1_id=col.ref(UserSpec, "admin"),
    ):
        col.add(
            ModuleSpec(
                key="module_5",
                module_id=5,
                title="Title of Module 5",
                description="Description of Module 5",
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
                        key="mod_5_gebiedengroep_510",
                        object_id=510,
                        title="Gebiedengroep 510 in Module 5",
                    ),
                    ModuleGebiedSpec(
                        key="mod_5_gebied_510",
                        object_id=510,
                        title="Gebied 510 in Module 5",
                    ),
                    ModuleGebiedsaanwijzingSpec(
                        key="mod_5_gebiedsaanwijzing_510",
                        object_id=510,
                        title="Gebiedsaanwijzing 510 in Module 5",
                    ),
                    # Removed from the module (did not really exists but this will handle the case anyways)
                    ModuleGebiedSpec(
                        key="mod_5_gebied_511",
                        object_id=511,
                        title="Gebied 511 hidden in Module 5",
                        context_hidden=True,
                    ),
                    # Terminated in the module
                    ModuleGebiedSpec(
                        key="mod_5_gebied_1",
                        object_id=1,
                        title="Gebied 1 terminated in Module 5",
                        context_action=ModuleObjectActionFull.Terminate,
                    ),
                    # Terminated in the module, but removed from the module again
                    # so the module does not terminate it anymore
                    ModuleGebiedSpec(
                        key="mod_5_gebied_3",
                        object_id=3,
                        title="Gebied 3 terminated and removed in Module 5",
                        context_action=ModuleObjectActionFull.Terminate,
                        context_hidden=True,
                    ),
                ]
            )

            col.adds(
                [
                    # Edit of the live beleidskeuze-1
                    ModuleBeleidskeuzeSpec(
                        key="mod_5_beleidskeuze_1_first_entry",
                        object_id=1,
                    ),
                    # New beleidskeuze, so it has no live version yet
                    ModuleBeleidskeuzeSpec(
                        key="mod_5_beleidskeuze_510_first_entry",
                        object_id=510,
                        title="Beleidskeuze 510 from module 5",
                        description="Description of beleidskeuze 510",
                        explanation="Explanation of beleidskeuze 510",
                        owner_1_id=col.ref(UserSpec, "owner-1"),
                    ),
                ]
            )
            col.adds(
                [
                    ModuleMaatregelSpec(
                        key="mod_5_maatregel_1_first_entry",
                        object_id=1,
                    ),
                ]
            )
