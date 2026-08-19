import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field, PrivateAttr

from app.core.db.base import Base

DATETIME_T0 = datetime(2025, 1, 1, tzinfo=UTC)

UUID_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000000")

BASE_FILES_DIR = Path(__file__).parent.parent / "data/files"


type PrimaryKey = uuid.UUID | int


class Spec(BaseModel):
    key: str | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        raise NotImplementedError()

    def get_link_fields(self) -> set[str]:
        fields: set[str] = set()
        for class_type in type(self).__mro__:
            fields |= class_type.__dict__.get("__link_fields__", set())
        return fields

    model_config = {"arbitrary_types_allowed": True}


class HasDefaults(Protocol):
    _defaults: dict[str, Any]
    _timepoint: datetime

    def _apply_defaults(self, data: dict[str, Any]) -> None: ...


class HasCurrentModule(Protocol):
    _current_module_id: int | None


@dataclass(frozen=True)
class Ref:
    spec_type: type[Spec]
    key: str


type Link = Ref | PrimaryKey


class FixtureCtx(BaseModel):
    module: int | None
    defaults: dict[str, Any]


class Record[T: Spec](BaseModel):
    spec: T
    ctx: FixtureCtx


# For the PersistService
class PersistContext(BaseModel):
    seen_codes: set[str] = set()
    # (Module_ID, Code)
    seen_module_context: set[tuple[int, str]] = set()


class BasePersistHandler[T: Spec]:
    def to_rows(self, record: Record[T], context: PersistContext) -> Sequence[Base]:
        raise NotImplementedError()


class PersistRecord[S: Spec, B: Base](BaseModel):
    spec: S
    rows: list[B]
    primary_key: PrimaryKey
    fixture_key: str | None
    fixture_ref: Ref | None

    model_config = {"arbitrary_types_allowed": True}


# The final conclusion given to the test system
class FixtureData(BaseModel):
    _lookup: dict[Ref, PersistRecord] = PrivateAttr(default_factory=dict)
    records: list[PersistRecord] = Field(default_factory=list)

    def model_post_init(self, context: Any) -> None:
        self._lookup = {record.fixture_ref: record for record in self.records if record.fixture_ref is not None}

    def find(self, ref: Ref) -> PersistRecord:
        record: PersistRecord | None = self._lookup.get(ref)
        if record is None:
            raise KeyError(f"No fixture record for {ref!r}")
        return record

    def find_uuids(self, refs: list[Ref]) -> list[uuid.UUID]:
        return [self.primary_key_uuid(ref) for ref in refs]

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
