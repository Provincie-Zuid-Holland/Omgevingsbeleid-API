from datetime import UTC, datetime, timedelta


def assert_same_datetime(actual: datetime, expected: datetime | None = None):
    expected = expected or datetime.now(UTC)
    difference: timedelta = abs(actual.replace(tzinfo=None) - expected.replace(tzinfo=None))
    assert difference <= timedelta(milliseconds=1), f"{actual} differs {difference} from {expected}"
