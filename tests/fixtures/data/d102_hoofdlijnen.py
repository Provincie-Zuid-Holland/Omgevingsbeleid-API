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
                    Name="Provinciaal economische groei",
                    Type="Gebiedsprogramma",
                    Created_Date=datetime(2025, 1, 1, tzinfo=UTC),
                ),
                HoofdlijnSpec(
                    key="hoofdlijn-2",
                    Name="Regionaal Waterprogramma",
                    Type="Verplicht programma",
                    Created_Date=datetime(2025, 1, 2, tzinfo=UTC),
                ),
            ]
        )
