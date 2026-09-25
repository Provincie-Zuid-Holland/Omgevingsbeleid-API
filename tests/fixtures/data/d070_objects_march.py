from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec, BeleidskeuzeSpec, GebiedSpec, MaatregelSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        # We explicitly do not set a default Created_Data
        # this way the created_date of the previous version will be used
        # as this is the same behaviour as the real code
        modified_date=datetime(2025, 3, 1, tzinfo=UTC),
        start_validity=datetime(2025, 3, 1, tzinfo=UTC),
        modified_by_id=col.ref(UserSpec, "ambtenaar"),
    ):
        # Beleidsdoel
        col.adds(
            [
                BeleidsdoelSpec(
                    key="beleidsdoel_1_latest_valid",
                    object_id=1,
                    title="Beleidsdoel 1 from march",
                ),
                BeleidsdoelSpec(
                    key="beleidsdoel_2_latest_valid",
                    object_id=2,
                    title="Beleidsdoel 2 from march",
                ),
                BeleidsdoelSpec(
                    key="beleidsdoel_3_latest_valid",
                    object_id=3,
                    title="Beleidsdoel 3 from march",
                ),
            ]
        )

        # Beleidskeuze
        col.adds(
            [
                # Attached to beleidsdoel-1
                BeleidskeuzeSpec(
                    key="beleidskeuze_1_latest_valid",
                    object_id=1,
                    title="Beleidskeuze 1 from march",
                ),
                BeleidskeuzeSpec(
                    object_id=2,
                    title="Beleidskeuze 2 from march",
                ),
                # Attached to beleidsdoel-2
                BeleidskeuzeSpec(
                    object_id=3,
                    title="Beleidskeuze 3 from march",
                ),
                BeleidskeuzeSpec(
                    object_id=4,
                    title="Beleidskeuze 4 from march",
                ),
            ]
        )

        # Maatregel
        col.adds(
            [
                # Attached to beleidskeuze-1
                MaatregelSpec(
                    key="maatregel_1_latest_valid",
                    object_id=1,
                    title="Maatregel 1 from march",
                ),
                # Attached to beleidskeuze-2
                MaatregelSpec(
                    object_id=2,
                    title="Maatregel 2 from march",
                ),
                MaatregelSpec(
                    object_id=3,
                    title="Maatregel 3 from march",
                ),
                # Attached to beleidskeuze-3
                MaatregelSpec(
                    object_id=4,
                    title="Maatregel 4 from march",
                ),
                MaatregelSpec(
                    object_id=5,
                    title="Maatregel 5 from march",
                ),
                # Past end_validity
                MaatregelSpec(
                    key="maatregel_6_past_end_validity",
                    object_id=6,
                    title="Maatregel 6 from march",
                    end_validity=datetime(2025, 6, 1, tzinfo=UTC),
                ),
            ]
        )

        # Gebied
        col.adds(
            [
                # Past end_validity, so it is not vigerend anymore
                GebiedSpec(
                    key="gebied_4_past_end_validity",
                    object_id=4,
                    title="Gebied 4 from march",
                    end_validity=datetime(2025, 6, 1, tzinfo=UTC),
                ),
            ]
        )
