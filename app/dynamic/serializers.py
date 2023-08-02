from typing import Any, Optional
from uuid import UUID


def serializer_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def serializer_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return serializer_str(value)


def serializer_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(value)


def serializer_optional_uuid(value: Any) -> Optional[UUID]:
    if value is None:
        return None
    return serializer_uuid(value)
