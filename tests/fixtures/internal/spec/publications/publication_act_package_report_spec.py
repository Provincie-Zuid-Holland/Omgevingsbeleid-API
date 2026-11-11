import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar, cast

from app.core.db import Base
from app.core.tables.publications import PublicationActPackageReportTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.spec.publications.package_report_file import ParsedReportFile, parse_report_file
from tests.fixtures.internal.spec.publications.publication_act_package_spec import PublicationActPackageSpec
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Ref,
    Spec,
)


class PublicationActPackageReportSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "act_package_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    act_package_id: Link
    file_path: str

    # These will be filled from the report file
    # `sub_delivery_id` is taken from the package when `act_package_id` is a Ref
    report_status: str = ""
    filename: str = ""
    source_document: str = ""
    main_outcome: str = ""
    sub_delivery_id: str = ""
    sub_progress: str = ""
    sub_outcome: str = ""

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationActPackageReportPrefillHandler(BasePrefillHandler[PublicationActPackageReportSpec]):
    def fill(
        self, record: Record[PublicationActPackageReportSpec], context: PrefillContext
    ) -> Record[PublicationActPackageReportSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        report: ParsedReportFile = parse_report_file(record.spec.file_path)
        record.spec.report_status = report.report_status
        record.spec.filename = report.filename
        record.spec.source_document = report.source_document
        record.spec.main_outcome = report.main_outcome
        record.spec.sub_delivery_id = report.sub_delivery_id
        record.spec.sub_progress = report.sub_progress
        record.spec.sub_outcome = report.sub_outcome

        package_ref: Link = record.spec.act_package_id
        if isinstance(package_ref, Ref):
            assert package_ref.spec_type == PublicationActPackageSpec
            package = cast(Record[PublicationActPackageSpec], context.find(package_ref))
            assert package.spec.delivery_id, "`delivery_id` of the package is expected to be set at this stage."
            record.spec.sub_delivery_id = package.spec.delivery_id

        return record


class PublicationActPackageReportPersistHandler(BasePersistHandler[PublicationActPackageReportSpec]):
    def to_rows(self, record: Record[PublicationActPackageReportSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationActPackageReportSpec = record.spec
        return [
            PublicationActPackageReportTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                act_package_id=spec.act_package_id,
                report_status=spec.report_status,
                filename=spec.filename,
                source_document=spec.source_document,
                main_outcome=spec.main_outcome,
                sub_delivery_id=spec.sub_delivery_id,
                sub_progress=spec.sub_progress,
                sub_outcome=spec.sub_outcome,
            )
        ]
