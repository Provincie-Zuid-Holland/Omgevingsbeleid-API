from datetime import datetime, timezone

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec, BeleidskeuzeSpec, MaatregelSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        # We explicitly do not set a default Created_Data
        # this way the Created_Date of the previous version will be used
        # as this is the same behaviour as the real code
        Modified_Date=datetime(2025, 3, 1, tzinfo=timezone.utc),
        Start_Validity=datetime(2025, 3, 1, tzinfo=timezone.utc),
        Modified_By_UUID=col.ref(UserSpec, "ambtenaar"),
    ):
        # Beleidsdoel
        col.adds(
            [
                BeleidsdoelSpec(
                    Object_ID=1,
                    Title="Beleidsdoel 1 from march",
                ),
                BeleidsdoelSpec(
                    Object_ID=2,
                    Title="Beleidsdoel 2 from march",
                ),
                BeleidsdoelSpec(
                    Object_ID=3,
                    Title="Beleidsdoel 3 from march",
                ),
            ]
        )

        # Beleidskeuze
        col.adds(
            [
                # Attached to beleidsdoel-1
                BeleidskeuzeSpec(
                    Object_ID=1,
                    Title="Beleidskeuze 1 from march",
                ),
                BeleidskeuzeSpec(
                    Object_ID=2,
                    Title="Beleidskeuze 2 from march",
                ),
                # Attached to beleidsdoel-2
                BeleidskeuzeSpec(
                    Object_ID=3,
                    Title="Beleidskeuze 3 from march",
                ),
                BeleidskeuzeSpec(
                    Object_ID=4,
                    Title="Beleidskeuze 4 from march",
                ),
            ]
        )

        # Maatregel
        col.adds(
            [
                # Attached to beleidskeuze-1
                MaatregelSpec(
                    Object_ID=1,
                    Title="Maatregel 1 from march",
                ),
                # Attached to beleidskeuze-2
                MaatregelSpec(
                    Object_ID=2,
                    Title="Maatregel 2 from march",
                ),
                MaatregelSpec(
                    Object_ID=3,
                    Title="Maatregel 3 from march",
                ),
                # Attached to beleidskeuze-3
                MaatregelSpec(
                    Object_ID=4,
                    Title="Maatregel 4 from march",
                ),
                MaatregelSpec(
                    Object_ID=5,
                    Title="Maatregel 5 from march",
                ),
                MaatregelSpec(
                    Object_ID=6,
                    Title="Maatregel 6 from march",
                ),
            ]
        )
