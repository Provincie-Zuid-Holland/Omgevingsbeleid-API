from datetime import datetime
from typing import Dict, List
from uuid import UUID
from .types import Field, FieldType


FIELD_TYPES: Dict[str, FieldType] = {
    ft.id: ft
    for ft in [
        FieldType(id="int", field_type=int, default=0),
        FieldType(id="float", field_type=float, default=0.0),
        FieldType(id="str", field_type=str, default=""),
        FieldType(id="uuid", field_type=UUID, default=UUID("00000000-0000-0000-0000-000000000000")),
        FieldType(id="datetime", field_type=datetime, default=datetime(1970, 1, 1)),
        FieldType(id="list_str", field_type=List[str], default=[]),
    ]
}


BASE_FIELDS = [
    Field(
        id="object_id",
        column="object_id",
        name="Object_ID",
        type="int",
        optional=False,
        validators=[],
        formatters=[],
    ),
    Field(
        id="uuid",
        column="uuid",
        name="UUID",
        type="uuid",
        optional=False,
    ),
    Field(
        id="object_type",
        column="object_type",
        name="Object_Type",
        type="str",
        optional=False,
    ),
    Field(
        id="code",
        column="code",
        name="Code",
        type="str",
        optional=False,
    ),
    Field(
        id="created_date",
        column="created_date",
        name="Created_Date",
        type="datetime",
        optional=False,
    ),
    Field(
        id="modified_date",
        column="modified_date",
        name="Modified_Date",
        type="datetime",
        optional=False,
    ),
    Field(
        id="adjust_on",
        column="adjust_on",
        name="Adjust_On",
        type="uuid",
        optional=True,
    ),
    Field(
        id="created_by_uuid",
        column="created_by_uuid",
        name="Created_By_UUID",
        type="uuid",
        optional=False,
        validators=[],
        formatters=[],
    ),
    Field(
        id="modified_by_uuid",
        column="modified_by_uuid",
        name="Modified_By_UUID",
        type="uuid",
        optional=False,
        validators=[],
        formatters=[],
    ),
    Field(
        id="start_validity",
        column="start_validity",
        name="Start_Validity",
        type="datetime",
        optional=True,
    ),
    Field(
        id="end_validity",
        column="end_validity",
        name="End_Validity",
        type="datetime",
        optional=True,
    ),
]
