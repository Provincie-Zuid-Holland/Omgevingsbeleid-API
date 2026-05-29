from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.ambitie_spec import AmbitieSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    col.add(
        AmbitieSpec(
            key="base",
            Object_ID=100,
            Title="First Title!",
        )
    )

    col.move_at(days=20)
    col.add(
        AmbitieSpec(
            Object_ID=100,
            Description="Finaly a description",
        )
    )

    col.move_at(days=1)
    with col.with_defaults(Modified_By_UUID=col.ref(UserSpec, "frozen")):
        col.add(
            AmbitieSpec(
                Object_ID=100,
                Title="Finally a new title!",
                Description="Changed a description",
            )
        )

    col.move_at(days=1)
    col.add(
        AmbitieSpec(
            Object_ID=100,
            Description="Final description",
            Adjust_On=col.ref(AmbitieSpec, "base"),
        )
    )
