import uuid
from datetime import datetime


def parse_datetime(date_str):
    # json doesn't support datetime, so parse it manually
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
    return None


def parse_date(date_str):
    # json doesn't support datetime, so parse it manually
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d")
    return None


def parse_uuid(uuid_str):
    # json doesn't support uuid, so parse it manually
    if uuid_str:
        return uuid.UUID(uuid_str)
    return None


def filter_valid_fields(class_type, item_dict):
    # Filter out fields that are not in the table for polymorphic classes (OW)
    valid_fields = {column.name for column in class_type.__table__.columns}
    return {k: v for k, v in item_dict.items() if v is not None and k in valid_fields}
