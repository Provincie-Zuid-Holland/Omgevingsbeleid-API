from datetime import UTC, datetime
from uuid import UUID

from .types import Field, FieldType

FIELD_TYPES: dict[str, FieldType] = {
    ft.id: ft
    for ft in [
        FieldType(id="int", field_type=int, default=0),
        FieldType(id="float", field_type=float, default=0.0),
        FieldType(id="str", field_type=str, default=""),
        FieldType(id="uuid", field_type=UUID, default=None),
        FieldType(id="datetime", field_type=datetime, default=datetime(1970, 1, 1, tzinfo=UTC)),
        FieldType(id="list_str", field_type=list[str], default=[]),
    ]
}


BASE_FIELDS = [
    Field(
        id="object_id",
        column="object_id",
        name="object_id",
        type="int",
        optional=False,
        validators=[],
        formatters=[],
    ),
    Field(
        id="id",
        column="id",
        name="id",
        type="uuid",
        optional=False,
    ),
    Field(
        id="object_type",
        column="object_type",
        name="object_type",
        type="str",
        optional=False,
    ),
    Field(
        id="code",
        column="code",
        name="code",
        type="str",
        optional=False,
    ),
    Field(
        id="created_date",
        column="created_date",
        name="created_date",
        type="datetime",
        optional=False,
    ),
    Field(
        id="modified_date",
        column="modified_date",
        name="modified_date",
        type="datetime",
        optional=False,
    ),
    Field(
        id="adjust_on",
        column="adjust_on",
        name="adjust_on",
        type="uuid",
        optional=True,
    ),
    Field(
        id="created_by_id",
        column="created_by_id",
        name="created_by_id",
        type="uuid",
        optional=False,
        validators=[],
        formatters=[],
    ),
    Field(
        id="modified_by_id",
        column="modified_by_id",
        name="modified_by_id",
        type="uuid",
        optional=False,
        validators=[],
        formatters=[],
    ),
    Field(
        id="start_validity",
        column="start_validity",
        name="start_validity",
        type="datetime",
        optional=True,
    ),
    Field(
        id="end_validity",
        column="end_validity",
        name="end_validity",
        type="datetime",
        optional=True,
    ),
]
