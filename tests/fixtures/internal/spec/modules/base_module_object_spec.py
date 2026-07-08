from typing import ClassVar, Optional, Set, Tuple, Type, TypeVar, Union

from app.api.domains.modules.types import ModuleObjectActionFull
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable
from tests.fixtures.internal.types import Record
from tests.fixtures.internal.spec.objects.beleidsdoel_spec import BaseObjectSpec
import uuid

from typing import Any, Dict, List, Sequence, cast


from app.core.db.base import Base
from app.core.tables.objects import ObjectStaticsTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    Spec,
    Ref,
    BasePersistHandler,
    PersistContext,
)


class BaseModuleObjectSpec(BaseObjectSpec):
    # This is the spec of the vigerend version, ex: for ModuleBeleidsdoelSpec it would be BeleidsdoelSpec
    # This is used to find the adjusted on it it does not exists in the module, and none was explicitly set
    __vigerend_spec__: ClassVar[Type[BaseObjectSpec]] = BaseObjectSpec

    __object_type__: ClassVar[str] = ""
    __object_fields__: ClassVar[Set[str]] = {
        "Module_ID",
        "Deleted",
    }

    Module_ID: int = 0
    Deleted: Optional[bool] = None

    # These fields are for the ModuleObjectContextTable
    Context_Hidden: Optional[bool] = None
    Context_Action: Optional[ModuleObjectActionFull] = None
    Context_Explanation: str = ""
    Context_Conclusion: str = ""

    def get_vigerend_spec(self) -> Type[BaseObjectSpec]:
        return self.__vigerend_spec__


T = TypeVar("T", bound=BaseModuleObjectSpec)


class BaseModuleObjectPrefillHandler(BasePrefillHandler[T]):
    def fill(self, record: Record[T], context: PrefillContext) -> Record[T]:
        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid4()

        previous_version: Optional[Record[Union[T, BaseObjectSpec]]] = self._find_previous(
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

        record = super().fill(record, context)

        return record

    def _find_previous(
        self, current_record: Record[T], previous_records: List[Record[Spec]]
    ) -> Optional[Record[Union[T, BaseObjectSpec]]]:
        previous: Optional[Record[Union[T, BaseObjectSpec]]] = (
            self._find_previous_by_type(
                current_record, previous_records, type(current_record.spec)
            )  # Lazy so we only search for vigerend if above result was None
            or self._find_previous_by_type(current_record, previous_records, current_record.spec.get_vigerend_spec())
        )

        return previous

    def _find_previous_by_type(
        self,
        current_record: Record[T],
        previous_records: List[Record[Spec]],
        target_spec_type: Type[Union[T, BaseObjectSpec]],
    ) -> Optional[Record[Union[T, BaseObjectSpec]]]:
        for previous_record in reversed(previous_records):
            if type(previous_record.spec) is not target_spec_type:
                continue

            previous_record_casted = cast(Record[Union[T, BaseObjectSpec]], previous_record)

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


class BaseModuleObjectPersistHandler[T: BaseModuleObjectSpec](BasePersistHandler[T]):
    def to_rows(self, record: Record[T], context: PersistContext) -> Sequence[Base]:
        spec: T = record.spec
        result: List[Base] = []

        if spec.Code not in context.seen_codes:
            context.seen_codes.add(spec.Code)
            result.append(self._build_object_static(spec))

        module_context_index: Tuple[int, int] = (spec.Module_ID, spec.Object_ID)
        if module_context_index not in context.seen_module_context:
            context.seen_module_context.add(module_context_index)
            result.append(self._build_module_object_context(spec))

        result.append(self._build_object(spec))

        return result

    def _build_object_static(self, spec: T) -> ObjectStaticsTable:
        data: Dict[str, Any] = {field: getattr(spec, field) for field in spec.get_static_fields()}

        return ObjectStaticsTable(**data)

    def _build_object(self, spec: T) -> ModuleObjectsTable:
        data: Dict[str, Any] = {field: getattr(spec, field) for field in spec.get_object_fields()}

        return ModuleObjectsTable(**data)

    def _build_module_object_context(self, spec: T) -> ModuleObjectContextTable:
        return ModuleObjectContextTable(
            Module_ID=spec.Module_ID,
            Object_Type=spec.Object_Type,
            Object_ID=spec.Object_ID,
            Code=spec.Code,
            Original_Adjust_On=spec.Adjust_On,
            Hidden=spec.Context_Hidden or False,
            Action=self._resolve_action(spec),
            Explanation=spec.Context_Explanation,
            Conclusion=spec.Context_Conclusion,
            Created_Date=spec.Created_Date,
            Modified_Date=spec.Modified_Date,
            Created_By_UUID=spec.Created_By_UUID,
            Modified_By_UUID=spec.Modified_By_UUID,
        )

    def _resolve_action(self, spec: T) -> ModuleObjectActionFull:
        if spec.Context_Action is not None:
            spec.Context_Action

        if spec.Adjust_On is None:
            return ModuleObjectActionFull.Create

        return ModuleObjectActionFull.Edit
