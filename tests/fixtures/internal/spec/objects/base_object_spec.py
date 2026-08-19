import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, ClassVar, Self, TypeVar, cast

from pydantic import model_validator

from app.core.db.base import Base
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Ref,
    Spec,
)


class BaseObjectSpec(Spec):
    # This will handle the Object_Type and that it is not overwritten by the users
    __object_type__: ClassVar[str] = ""
    __inheritable__: ClassVar[set[str]] = {
        "Created_Date",
        "Created_By_UUID",
        "Start_Validity",
        "End_Validity",
    }
    __link_fields__: ClassVar[set[str]] = {
        "Adjust_On",
        "Created_By_UUID",
        "Modified_By_UUID",
        "Owner_1_UUID",
        "Owner_2_UUID",
        "Portfolio_Holder_1_UUID",
        "Portfolio_Holder_2_UUID",
        "Client_1_UUID",
    }
    __object_fields__: ClassVar[set[str]] = {
        "Object_ID",
        "Object_Type",
        "Code",
        "UUID",
        "Adjust_On",
        "Created_Date",
        "Created_By_UUID",
        "Modified_Date",
        "Modified_By_UUID",
        "Start_Validity",
        "End_Validity",
    }
    __static_fields__: ClassVar[set[str]] = {
        "Object_ID",
        "Object_Type",
        "Code",
        "Owner_1_UUID",
        "Owner_2_UUID",
        "Portfolio_Holder_1_UUID",
        "Portfolio_Holder_2_UUID",
        "Client_1_UUID",
    }

    Object_ID: int = 0
    Object_Type: str = ""
    Code: str = ""
    UUID: uuid.UUID | None = None
    Adjust_On: Link | None = None
    Created_Date: datetime | None = None
    Created_By_UUID: Link | None = None
    Modified_Date: datetime | None = None
    Modified_By_UUID: Link | None = None
    Start_Validity: datetime | None = None
    End_Validity: datetime | None = None
    Owner_1_UUID: Link | None = None
    Owner_2_UUID: Link | None = None
    Portfolio_Holder_1_UUID: Link | None = None
    Portfolio_Holder_2_UUID: Link | None = None
    Client_1_UUID: Link | None = None

    @model_validator(mode="before")
    def ensure_fixed_object_type(cls, data: Any):
        data["Object_Type"] = cls.__object_type__
        return data

    @model_validator(mode="after")
    def ensure_object_id_code(self) -> Self:
        # Everything is already set
        if self.Object_ID and self.Code:
            return self

        if self.Code:
            self.Object_ID = self._resolve_object_id(self.Code)
            return self

        self.Code = f"{self.Object_Type}-{self.Object_ID}"
        return self

    def _resolve_object_id(self, code: str) -> int:
        try:
            _, object_id_str = code.split("-", 1)
            object_id = int(object_id_str)
            return object_id
        except ValueError:
            raise RuntimeError(f"Invalid format for Object Code `{code}`")

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID

    def get_ref(self) -> Ref | None:
        if self.key is None:
            return None

        return Ref(
            spec_type=type(self),
            key=self.key,
        )

    def get_inheritable_fields(self) -> set[str]:
        return self._get_fields_for_key("__inheritable__")

    def get_object_fields(self) -> set[str]:
        return self._get_fields_for_key("__object_fields__")

    def get_static_fields(self) -> set[str]:
        return self._get_fields_for_key("__static_fields__")

    def _get_fields_for_key(self, key: str) -> set[str]:
        fields: set[str] = set()
        for class_type in type(self).__mro__:
            fields |= class_type.__dict__.get(key, set())
        return fields


T = TypeVar("T", bound=BaseObjectSpec)


class BaseObjectPrefillHandler(BasePrefillHandler[T]):
    def fill(self, record: Record[T], context: PrefillContext) -> Record[T]:
        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid4()

        record = super().fill(record, context)

        previous_version: Record[T] | None = self._find_previous(
            record,
            context.previous_records,
        )
        if previous_version is not None:
            record.spec.Adjust_On = previous_version.spec.UUID
            for field_name in record.spec.get_inheritable_fields():
                if field_name not in record.spec.model_fields_set:
                    prev_value = getattr(previous_version.spec, field_name)
                    if prev_value is not None:
                        setattr(record.spec, field_name, prev_value)

        return record

    def _find_previous(self, current_record: Record[T], previous_records: list[Record[Spec]]) -> Record[T] | None:
        for previous_record in reversed(previous_records):
            if type(previous_record.spec) is not type(current_record.spec):
                continue

            previous_record_casted = cast(Record[T], previous_record)

            # Find based on what we have
            # If we have a Adjust_On, then we must find where we are pointing to
            match current_record.spec.Adjust_On:
                case None:
                    # Search for code
                    if previous_record.spec.Code == current_record.spec.Code:
                        return previous_record_casted
                case Ref():
                    if previous_record.spec.get_ref() == current_record.spec.Adjust_On:
                        return previous_record_casted
                case uuid.UUID() | int() as pk:
                    if previous_record.spec.get_table_primary_key() == pk:
                        return previous_record_casted
        return None


class BaseObjectPersistHandler[T: BaseObjectSpec](BasePersistHandler[T]):
    def to_rows(self, record: Record[T], context: PersistContext) -> Sequence[Base]:
        spec: T = record.spec
        result: list[Base] = []

        if spec.Code not in context.seen_codes:
            context.seen_codes.add(spec.Code)
            result.append(self._build_object_static(spec))

        result.append(self._build_object(spec))

        return result

    def _build_object_static(self, spec: T) -> ObjectStaticsTable:
        data: dict[str, Any] = {field: getattr(spec, field) for field in spec.get_static_fields()}

        return ObjectStaticsTable(**data)

    def _build_object(self, spec: T) -> ObjectsTable:
        data: dict[str, Any] = {field: getattr(spec, field) for field in spec.get_object_fields()}

        return ObjectsTable(**data)
