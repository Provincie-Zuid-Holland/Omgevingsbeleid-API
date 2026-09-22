from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Modified_Date=datetime(2025, 1, 1, tzinfo=UTC),
        Created_By_UUID=col.ref(UserSpec, "ambtenaar"),
        Modified_By_UUID=col.ref(UserSpec, "ambtenaar"),
    ):
        col.adds(
            [
                HoofdlijnSpec(
                    key="hoofdlijn-1",
                    name="Provinciaal economische groei",
                    type="Verplicht programma",
                    Created_Date=datetime(2025, 1, 2, tzinfo=UTC),
                ),
                HoofdlijnSpec(
                    key="hoofdlijn-2",
                    name="Regionaal waterprogramma",
                    type="Gebiedsprogramma",
                    Created_Date=datetime(2025, 1, 3, tzinfo=UTC),
                ),
                HoofdlijnSpec(
                    key="hoofdlijn-3",
                    name="Provinciaal waterprogramma",
                    type="Actief programma",
                    Created_Date=datetime(2025, 1, 4, tzinfo=UTC),
                ),
            ]
        )
