from datetime import datetime, timezone

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.spec.area_spec import AreaSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec
from tests.fixtures.internal.spec.objects import (
    BeleidsdoelSpec,
    BeleidskeuzeSpec,
    MaatregelSpec,
    GebiedSpec,
    GebiedengroepSpec,
)


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_Date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        Modified_Date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        Start_Validity=datetime(2025, 1, 1, tzinfo=timezone.utc),
        Created_By_UUID=col.ref(UserSpec, "ambtenaar"),
        Modified_By_UUID=col.ref(UserSpec, "ambtenaar"),
    ):
        # Beleidsdoel
        col.adds(
            [
                BeleidsdoelSpec(
                    Object_ID=1,
                    Title="Beleidsdoel 1 from januari",
                    Description="Description of beleidsdoel 1",
                    Owner_1_UUID=col.ref(UserSpec, "owner-1"),
                ),
                BeleidsdoelSpec(
                    Object_ID=2,
                    Title="Beleidsdoel 2 from januari",
                    Description="Description of beleidsdoel 2",
                ),
                BeleidsdoelSpec(
                    Object_ID=3,
                    Title="Beleidsdoel 3 from januari",
                    Description="Description of beleidsdoel 3",
                ),
            ]
        )

        # Beleidskeuze
        col.adds(
            [
                # Attached to beleidsdoel-1
                BeleidskeuzeSpec(
                    Object_ID=1,
                    Title="Beleidskeuze 1 from januari",
                    Description="Description of beleidskeuze 1",
                    Explanation="Explanation of beleidskeuze 1",
                    Hierarchy_Code="beleidsdoel-1",
                    Portfolio_Holder_1_UUID=col.ref(UserSpec, "owner-1"),
                ),
                BeleidskeuzeSpec(
                    Object_ID=2,
                    Title="Beleidskeuze 2 from januari",
                    Description="Description of beleidskeuze 2",
                    Explanation="Explanation of beleidskeuze 2",
                    Hierarchy_Code="beleidsdoel-1",
                ),
                # Attached to beleidsdoel-2
                BeleidskeuzeSpec(
                    Object_ID=3,
                    Title="Beleidskeuze 3 from januari",
                    Description="Description of beleidskeuze 3",
                    Explanation="Explanation of beleidskeuze 3",
                    Hierarchy_Code="beleidsdoel-2",
                ),
                BeleidskeuzeSpec(
                    Object_ID=4,
                    Title="Beleidskeuze 4 from januari",
                    Description="Description of beleidskeuze 4",
                    Explanation="Explanation of beleidskeuze 4",
                    Hierarchy_Code="beleidsdoel-2",
                ),
            ]
        )

        # Maatregel
        col.adds(
            [
                # Attached to beleidskeuze-1
                MaatregelSpec(
                    Object_ID=1,
                    Title="Maatregel 1 from januari",
                    Description="Description of maatregel 1",
                    Effect="Effect of maatregel 1",
                    Hierarchy_Code="beleidskeuze-1",
                    Client_1_UUID=col.ref(UserSpec, "owner-1"),
                ),
                # Attached to beleidskeuze-2
                MaatregelSpec(
                    Object_ID=2,
                    Title="Maatregel 2 from januari",
                    Description="Description of maatregel 2",
                    Effect="Effect of maatregel 2",
                    Hierarchy_Code="beleidskeuze-2",
                ),
                MaatregelSpec(
                    Object_ID=3,
                    Title="Maatregel 3 from januari",
                    Description="Description of maatregel 3",
                    Effect="Effect of maatregel 3",
                    Hierarchy_Code="beleidskeuze-2",
                ),
                # Attached to beleidskeuze-3
                MaatregelSpec(
                    Object_ID=4,
                    Title="Maatregel 4 from januari",
                    Description="Description of maatregel 4",
                    Effect="Effect of maatregel 4",
                    Hierarchy_Code="beleidskeuze-3",
                ),
                MaatregelSpec(
                    Object_ID=5,
                    Title="Maatregel 5 from januari",
                    Description="Description of maatregel 5",
                    Effect="Effect of maatregel 5",
                    Hierarchy_Code="beleidskeuze-3",
                ),
                MaatregelSpec(
                    Object_ID=6,
                    Title="Maatregel 6 from januari",
                    Description="Description of maatregel 6",
                    Effect="Effect of maatregel 6",
                    Hierarchy_Code="beleidskeuze-3",
                ),
            ]
        )

        # Gebiedengroep Nature
        col.adds(
            [
                GebiedengroepSpec(
                    key="nature-v1",
                    Object_ID=1,
                    Title="Nature",
                    Description="Description of Natuur",
                    Gebieden=["gebied-1", "gebied-2"],
                    Source_Title="Nature",
                    Source_UUID=col.ref(InputGeoWerkingsgebiedenSpec, "nature-v1"),
                ),
                GebiedSpec(
                    key="nature-west-v1",
                    Object_ID=1,
                    Title="Nature West",
                    Area_UUID=col.ref(AreaSpec, "nature-west-v1"),
                ),
                GebiedSpec(
                    key="nature-east-v1",
                    Object_ID=2,
                    Title="Nature East",
                    Area_UUID=col.ref(AreaSpec, "nature-east-v1"),
                ),
                GebiedSpec(
                    key="nature-south-v1",
                    Object_ID=3,
                    Title="Nature South",
                    Area_UUID=col.ref(AreaSpec, "nature-south-v1"),
                ),
            ]
        )
