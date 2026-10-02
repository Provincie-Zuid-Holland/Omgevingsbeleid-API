from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.area_spec import AreaSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec
from tests.fixtures.internal.spec.objects import (
    BeleidsdoelSpec,
    BeleidskeuzeSpec,
    GebiedengroepSpec,
    GebiedSpec,
    MaatregelSpec,
)
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        created_date=datetime(2025, 1, 1, tzinfo=UTC),
        modified_date=datetime(2025, 1, 1, tzinfo=UTC),
        start_validity=datetime(2025, 1, 1, tzinfo=UTC),
        created_by_id=col.ref(UserSpec, "ambtenaar"),
        modified_by_id=col.ref(UserSpec, "ambtenaar"),
    ):
        # Beleidsdoel
        col.adds(
            [
                BeleidsdoelSpec(
                    object_id=1,
                    title="Beleidsdoel 1 from januari",
                    description="Description of beleidsdoel 1",
                    owner_1_id=col.ref(UserSpec, "owner-1"),
                ),
                BeleidsdoelSpec(
                    object_id=2,
                    title="Beleidsdoel 2 from januari",
                    description="Description of beleidsdoel 2",
                ),
                BeleidsdoelSpec(
                    object_id=3,
                    title="Beleidsdoel 3 from januari",
                    description="Description of beleidsdoel 3",
                ),
            ]
        )

        # Beleidskeuze
        col.adds(
            [
                # Attached to beleidsdoel-1
                BeleidskeuzeSpec(
                    object_id=1,
                    title="Beleidskeuze 1 from januari",
                    description="Description of beleidskeuze 1",
                    explanation="Explanation of beleidskeuze 1",
                    hierarchy_code="beleidsdoel-1",
                    portfolio_holder_1_id=col.ref(UserSpec, "owner-1"),
                ),
                BeleidskeuzeSpec(
                    object_id=2,
                    title="Beleidskeuze 2 from januari",
                    description="Description of beleidskeuze 2",
                    explanation="Explanation of beleidskeuze 2",
                    hierarchy_code="beleidsdoel-1",
                ),
                # Attached to beleidsdoel-2
                BeleidskeuzeSpec(
                    object_id=3,
                    title="Beleidskeuze 3 from januari",
                    description="Description of beleidskeuze 3",
                    explanation="Explanation of beleidskeuze 3",
                    hierarchy_code="beleidsdoel-2",
                ),
                BeleidskeuzeSpec(
                    object_id=4,
                    title="Beleidskeuze 4 from januari",
                    description="Description of beleidskeuze 4",
                    explanation="Explanation of beleidskeuze 4",
                    hierarchy_code="beleidsdoel-2",
                ),
            ]
        )

        # Maatregel
        col.adds(
            [
                # Attached to beleidskeuze-1
                MaatregelSpec(
                    object_id=1,
                    title="Maatregel 1 from januari",
                    description="Description of maatregel 1",
                    effect="Effect of maatregel 1",
                    hierarchy_code="beleidskeuze-1",
                    client_1_id=col.ref(UserSpec, "owner-1"),
                ),
                # Attached to beleidskeuze-2
                MaatregelSpec(
                    object_id=2,
                    title="Maatregel 2 from januari",
                    description="Description of maatregel 2",
                    effect="Effect of maatregel 2",
                    hierarchy_code="beleidskeuze-2",
                ),
                MaatregelSpec(
                    object_id=3,
                    title="Maatregel 3 from januari",
                    description="Description of maatregel 3",
                    effect="Effect of maatregel 3",
                    hierarchy_code="beleidskeuze-2",
                ),
                # Attached to beleidskeuze-3
                MaatregelSpec(
                    object_id=4,
                    title="Maatregel 4 from januari",
                    description="Description of maatregel 4",
                    effect="Effect of maatregel 4",
                    hierarchy_code="beleidskeuze-3",
                ),
                MaatregelSpec(
                    object_id=5,
                    title="Maatregel 5 from januari",
                    description="Description of maatregel 5",
                    effect="Effect of maatregel 5",
                    hierarchy_code="beleidskeuze-3",
                ),
                MaatregelSpec(
                    object_id=6,
                    title="Maatregel 6 from januari",
                    description="Description of maatregel 6",
                    effect="Effect of maatregel 6",
                    hierarchy_code="beleidskeuze-3",
                ),
            ]
        )

        # Gebiedengroep Nature
        col.adds(
            [
                GebiedengroepSpec(
                    key="nature-v1",
                    object_id=1,
                    title="Nature",
                    description="Description of Natuur",
                    gebieden=["gebied-1", "gebied-2"],
                    source_title="Nature",
                    source_uuid=col.ref(InputGeoWerkingsgebiedenSpec, "nature-v1"),
                ),
                GebiedSpec(
                    key="nature-west-v1",
                    object_id=1,
                    title="Nature West",
                    area_id=col.ref(AreaSpec, "nature-west-v1"),
                ),
                GebiedSpec(
                    key="nature-east-v1",
                    object_id=2,
                    title="Nature East",
                    area_id=col.ref(AreaSpec, "nature-east-v1"),
                ),
                GebiedSpec(
                    key="nature-south-v1",
                    object_id=3,
                    title="Nature South",
                    area_id=col.ref(AreaSpec, "nature-south-v1"),
                ),
            ]
        )
