from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db import Base
from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class AcknowledgedRelationSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {
        "created_by_id",
        "modified_by_id",
        "from_acknowledged_by_id",
        "to_acknowledged_by_id",
    }

    version: int = 1
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    requested_by_code: str
    from_code: str
    from_acknowledged: datetime | None = None
    from_acknowledged_by_id: Link | None = None
    from_explanation: str = ""
    to_code: str
    to_acknowledged: datetime | None = None
    to_acknowledged_by_id: Link | None = None
    to_explanation: str = ""

    denied: datetime | None = None
    deleted_at: datetime | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        return hash(f"{self.version}-{self.from_code}-{self.to_code}")


class AcknowledgedRelationPrefillHandler(BasePrefillHandler[AcknowledgedRelationSpec]):
    def fill(
        self, record: Record[AcknowledgedRelationSpec], context: PrefillContext
    ) -> Record[AcknowledgedRelationSpec]:
        record = super().fill(record, context)
        assert record.spec.from_code < record.spec.to_code, "`from_code` should sort before `to_code`"
        return record


class AcknowledgedRelationPersistHandler(BasePersistHandler[AcknowledgedRelationSpec]):
    def to_rows(self, record: Record[AcknowledgedRelationSpec], context: PersistContext) -> Sequence[Base]:
        spec: AcknowledgedRelationSpec = record.spec
        return [
            AcknowledgedRelationsTable(
                version=spec.version,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                modified_date=spec.modified_date,
                modified_by_id=spec.modified_by_id,
                requested_by_code=spec.requested_by_code,
                from_code=spec.from_code,
                from_acknowledged=spec.from_acknowledged,
                from_acknowledged_by_uuid=spec.from_acknowledged_by_id,
                from_explanation=spec.from_explanation,
                to_code=spec.to_code,
                to_acknowledged=spec.to_acknowledged,
                to_acknowledged_by_uuid=spec.to_acknowledged_by_id,
                to_explanation=spec.to_explanation,
                denied=spec.denied,
                deleted_at=spec.deleted_at,
            )
        ]
