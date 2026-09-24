from datetime import UTC, datetime, timedelta

from tests.fixtures.internal.types import Context, Ref, Spec


def assert_same_datetime(actual: datetime, expected: datetime | None = None):
    expected = expected or datetime.now(UTC)
    difference: timedelta = abs(actual.replace(tzinfo=None) - expected.replace(tzinfo=None))
    assert difference <= timedelta(milliseconds=1), f"{actual} differs {difference} from {expected}"


def get_uuids_from_spec(ctx: Context, spec_type: type[Spec], keys: list[str]) -> list[str]:
    return [str(ctx.f.primary_key_uuid(Ref(spec_type, key))) for key in keys]
