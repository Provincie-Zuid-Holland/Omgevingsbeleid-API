import uuid

from datetime import datetime
from typing import Any, ClassVar, List, Optional, Self, Set, TypeVar, cast

from pydantic import model_validator

from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import Spec, Link, PrimaryKey, UUID_NAMESPACE, Record, Ref


class BaseObjectSpec(Spec):
    # This will handle the Object_Type and that it is not overwritten by the users
    __object_type__: ClassVar[str] = ""
    __inheritable__: ClassVar[Set[str]] = {"Created_Date", "Created_By"}
    __link_fields__: ClassVar[Set[str]] = {"Adjust_On", "Created_By", "Modified_By"}

    Object_ID: Optional[int] = None
    Object_Type: str = ""
    Code: Optional[str] = None
    UUID: Optional[uuid.UUID] = None
    Adjust_On: Optional[Link] = None
    Created_Date: Optional[datetime] = None
    Created_By: Optional[Link] = None
    Modified_Date: Optional[datetime] = None
    Modified_By: Optional[Link] = None
    
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
    
    def get_ref(self) -> Optional[Ref]:
        if self.key is None:
            return None
        
        return Ref(
            spec_type=type(self),
            key=self.key,
        )

    def get_inheritable_fields(self) -> Set[str]:
        fields: Set[str] = set()
        for class_type in type(self).__mro__:
            fields |= class_type.__dict__.get("__inheritable__", set())
        return fields


class BaseModuleObjectSpec(BaseObjectSpec):
    Module_ID: Optional[int] = None


T = TypeVar("T", bound=BaseObjectSpec)


class BaseObjectPrefillHandler(BasePrefillHandler[T]):
    def fill(self, record: Record[T], context: PrefillContext) -> Record[T]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid5(UUID_NAMESPACE, f"{record.spec.Code}:{context.spec_count}")
        
        previous_version: Optional[Record[T]] = self._find_previous(
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

    def _find_previous(self, current_record: Record[T], previous_records: List[Record[Spec]]) -> Optional[Record[T]]:
        for previous_record in reversed(previous_records):
            if type(previous_record.spec) is not current_record.spec_type:
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
