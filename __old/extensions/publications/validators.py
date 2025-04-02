from datetime import date

from dateutil.parser import parse


def validate_effective_date(cls, v):
    if v is not None:
        effective_date = parse(v) if isinstance(v, str) else v
        if effective_date <= date.today():
            raise ValueError("Effective Date must be in the future")
    return v


def validate_announcement_date(cls, v, values, **kwargs):  # noqa
    if "Effective_Date" in values and v is not None:
        announcement_date = parse(v) if isinstance(v, str) else v
        effective_date = (
            parse(values["Effective_Date"]) if isinstance(values["Effective_Date"], str) else values["Effective_Date"]
        )
        if effective_date is not None and announcement_date >= effective_date:
            raise ValueError("Announcement Date must be earlier than Effective Date")

        if announcement_date <= date.today():
            raise ValueError("Announcement Date must in the future")

    return v
