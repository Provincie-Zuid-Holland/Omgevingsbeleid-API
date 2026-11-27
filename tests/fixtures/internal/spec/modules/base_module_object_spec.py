import uuid
from collections.abc import Sequence
from typing import Any, ClassVar, TypeVar, cast

from app.api.domains.modules.types import ModuleObjectActionFull
from app.core.db.base import Base
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable
from app.core.tables.objects import ObjectStaticsTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.spec.objects.beleidsdoel_spec import BaseObjectSpec
from tests.fixtures.internal.types import (
    BasePersistHandler,
    PersistContext,
    Record,
    Ref,
    Spec,
)


class BaseModuleObjectSpec(BaseObjectSpec):
    # This is the spec of the vigerend version, ex: for ModuleBeleidsdoelSpec it would be BeleidsdoelSpec
    # This is used to find the adjusted on it does not exist in the module, and none was explicitly set
    __vigerend_spec__: ClassVar[type[BaseObjectSpec]] = BaseObjectSpec

    __object_type__: ClassVar[str] = ""
    __object_fields__: ClassVar[set[str]] = {
        "module_id",
        "deleted",
    }

    module_id: int = 0
    deleted: bool | None = None

    # These fields are for the ModuleObjectContextTable
    context_hidden: bool | None = None
    context_action: ModuleObjectActionFull | None = None
    context_explanation: str = ""
    context_conclusion: str = ""

    def get_vigerend_spec(self) -> type[BaseObjectSpec]:
        return self.__vigerend_spec__


T = TypeVar("T", bound=BaseModuleObjectSpec)


class BaseModuleObjectPrefillHandler(BasePrefillHandler[T]):
    def fill(self, record: Record[T], context: PrefillContext) -> Record[T]:
        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        previous_version: Record[T | BaseObjectSpec] | None = self._find_previous(
            record,
            context.previous_records,
        )
        if previous_version is not None:
            record.spec.adjust_on = previous_version.spec.id
            for field_name in record.spec.get_inheritable_fields():
                if field_name not in record.spec.model_fields_set:
                    prev_value = getattr(previous_version.spec, field_name)
                    if prev_value is not None:
                        setattr(record.spec, field_name, prev_value)

        record = super().fill(record, context)

        return record

    def _find_previous(
        self, current_record: Record[T], previous_records: list[Record[Spec]]
    ) -> Record[T | BaseObjectSpec] | None:
        previous: Record[T | BaseObjectSpec] | None = (
            self._find_previous_by_type(
                current_record, previous_records, type(current_record.spec)
            )  # Lazy so we only search for vigerend if above result was None
            or self._find_previous_by_type(current_record, previous_records, current_record.spec.get_vigerend_spec())
        )

        return previous

    def _find_previous_by_type(
        self,
        current_record: Record[T],
        previous_records: list[Record[Spec]],
        target_spec_type: type[T | BaseObjectSpec],
    ) -> Record[T | BaseObjectSpec] | None:
        for previous_record in reversed(previous_records):
            if type(previous_record.spec) is not target_spec_type:
                continue

            previous_record_casted = cast(Record[T | BaseObjectSpec], previous_record)

            # Find based on what we have
            # If we have an adjust_on, then we must find where we are pointing to
            match current_record.spec.adjust_on:
                case None:
                    # Search for code
                    if previous_record.spec.code == current_record.spec.code:
                        return previous_record_casted
                case Ref():
                    if previous_record.spec.get_ref() == current_record.spec.adjust_on:
                        return previous_record_casted
                case uuid.UUID() | int() as pk:
                    if previous_record.spec.get_table_primary_key() == pk:
                        return previous_record_casted
        return None


class BaseModuleObjectPersistHandler[T: BaseModuleObjectSpec](BasePersistHandler[T]):
    def to_rows(self, record: Record[T], context: PersistContext) -> Sequence[Base]:
        spec: T = record.spec
        result: list[Base] = []

        if spec.code not in context.seen_codes:
            context.seen_codes.add(spec.code)
            result.append(self._build_object_static(spec))

        module_context_index: tuple[int, str] = (spec.module_id, spec.code)
        if module_context_index not in context.seen_module_context:
            context.seen_module_context.add(module_context_index)
            result.append(self._build_module_object_context(spec))

        result.append(self._build_object(spec))

        return result

    def _build_object_static(self, spec: T) -> ObjectStaticsTable:
        data: dict[str, Any] = {field: getattr(spec, field) for field in spec.get_static_fields()}

        return ObjectStaticsTable(**data)

    def _build_object(self, spec: T) -> ModuleObjectsTable:
        data: dict[str, Any] = {field: getattr(spec, field) for field in spec.get_object_fields()}

        return ModuleObjectsTable(**data)

    def _build_module_object_context(self, spec: T) -> ModuleObjectContextTable:
        return ModuleObjectContextTable(
            module_id=spec.module_id,
            object_type=spec.object_type,
            object_id=spec.object_id,
            code=spec.code,
            original_adjust_on=spec.adjust_on,
            hidden=spec.context_hidden or False,
            action=self._resolve_action(spec),
            explanation=spec.context_explanation,
            conclusion=spec.context_conclusion,
            created_date=spec.created_date,
            modified_date=spec.modified_date,
            created_by_id=spec.created_by_id,
            modified_by_id=spec.modified_by_id,
        )

    def _resolve_action(self, spec: T) -> ModuleObjectActionFull:
        if spec.context_action is not None:
            return spec.context_action

        if spec.adjust_on is None:
            return ModuleObjectActionFull.Create

        return ModuleObjectActionFull.Edit
