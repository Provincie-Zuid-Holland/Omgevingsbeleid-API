from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec, GebiedSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        # Never versions but valid only from 2099 (after "now")
        modified_date=datetime(2099, 1, 1, tzinfo=UTC),
        start_validity=datetime(2099, 1, 1, tzinfo=UTC),
        modified_by_id=col.ref(UserSpec, "ambtenaar"),
    ):
        col.adds(
            [
                BeleidsdoelSpec(
                    key="beleidsdoel_3_future",
                    object_id=3,
                    title="Beleidsdoel 3 from future",
                ),
                # New lineage which is not vigerend yet
                GebiedSpec(
                    key="gebied_5_future",
                    object_id=5,
                    title="Gebied 5 from future",
                ),
            ]
        )
