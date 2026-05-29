from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol, Set, Type, Union
import uuid

from pydantic import BaseModel


DATETIME_T0 = datetime(2025, 1, 1, tzinfo=timezone.utc)

UUID_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000000")


type PrimaryKey = Union[uuid.UUID, int]


class Spec(BaseModel):
    key: Optional[str] = None

    def get_table_primary_key(self) -> PrimaryKey:
        raise NotImplementedError()
    
    def get_link_fields(self) -> Set[str]:
        fields: Set[str] = set()
        for class_type in type(self).__mro__:
            fields |= class_type.__dict__.get("__link_fields__", set())
        return fields

    model_config = {"arbitrary_types_allowed": True}


class HasDefaults(Protocol):
    _defaults: Dict[str, Any]


class HasCurrentModule(Protocol):
    _current_module_id: Optional[int]


@dataclass(frozen=True)
class Ref:
    spec_type: Type[Spec]
    key: str


type Link = Union[Ref, PrimaryKey]


class FixtureCtx(BaseModel):
    module: Optional[int]
    defaults: Dict[str, Any]


class Record[T: Spec](BaseModel):
    spec: T
    spec_type: Type[T]
    ctx: FixtureCtx
