import datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.ambitie_spec import AmbitieSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import DATETIME_T0


def load(col: Collector) -> None:
    col.at(DATETIME_T0)
    col.set_defaults(
        Created_By=col.ref(UserSpec, "alice"),
        Modified_By=col.ref(UserSpec, "alice"),
    )
    col.add(
        AmbitieSpec(
            key="base",
            Object_ID=100,
            Title="First Title!",
        )
    )

    col.set_defaults(Created_By=col.ref(UserSpec, "admin"))
    col.at(DATETIME_T0 + datetime.timedelta(days=20))

    col.add(
        AmbitieSpec(
            Object_ID=100,
            Description="Finaly a description",
        )
    )

    with col.with_defaults(Created_By=col.ref(UserSpec, "frozen")):
        col.add(
            AmbitieSpec(
                Object_ID=100,
                Title="Finally a new title!",
                Description="Changed a description",
            )
        )
    
    col.add(
        AmbitieSpec(
            Object_ID=100,
            Description="Final description",
            Adjust_On=col.ref(AmbitieSpec, "base"),
        )
    )
