from datetime import datetime, timezone

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        # Never versions but valid only from 2099 (after "now")
        Modified_Date=datetime(2099, 1, 1, tzinfo=timezone.utc),
        Start_Validity=datetime(2099, 1, 1, tzinfo=timezone.utc),
        Modified_By_UUID=col.ref(UserSpec, "ambtenaar"),
    ):
        col.adds(
            [
                BeleidsdoelSpec(
                    Object_ID=3,
                    Title="Beleidsdoel 3 from future",
                ),
            ]
        )
