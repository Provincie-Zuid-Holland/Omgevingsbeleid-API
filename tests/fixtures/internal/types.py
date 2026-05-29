from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Sequence, Set, Type, Union
import uuid

from pydantic import BaseModel, Field, PrivateAttr

from app.core.db.base import Base


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
    ctx: FixtureCtx


# For the PersistService
class PersistContext(BaseModel):
    seen_codes: Set[str] = set()


class BasePersistHandler[T: Spec]:
    def to_rows(self, record: Record[T], context: PersistContext) -> Sequence[Base]:
        raise NotImplementedError()


class PersistRecord[S: Spec, B: Base](BaseModel):
    spec: S
    rows: List[B]
    primary_key: PrimaryKey
    fixture_key: Optional[str]
    fixture_ref: Optional[Ref]

    model_config = {"arbitrary_types_allowed": True}


# The final conclusion given to the test system
class FixtureData(BaseModel):
    _lookup: Dict[Ref, PersistRecord] = PrivateAttr(default_factory=dict)
    records: List[PersistRecord] = Field(default_factory=list)

    def model_post_init(self, context: Any) -> None:
        self._lookup = {record.fixture_ref: record for record in self.records if record.fixture_ref is not None}

    def find(self, ref: Ref) -> PersistRecord:
        record: Optional[PersistRecord] = self._lookup.get(ref)
        if record is None:
            raise KeyError(f"No fixture record for {ref!r}")
        return record

    def primary_key(self, ref: Ref) -> PrimaryKey:
        return self.find(ref).primary_key

    def primary_key_uuid(self, ref: Ref) -> uuid.UUID:
        primary_key: PrimaryKey = self.primary_key(ref)
        match primary_key:
            case uuid.UUID():
                return primary_key
            case _:
                raise RuntimeError(
                    f"The PrimaryKey `{primary_key}` is not a uuid.UUID but a `{type(self.primary_key)}`"
                )
