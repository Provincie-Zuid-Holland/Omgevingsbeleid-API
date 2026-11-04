from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.publications import (
    PublicationActPackageSpec,
    PublicationAnnouncementPackageSpec,
    PublicationAnnouncementSpec,
    PublicationPackageZipSpec,
    PublicationSpec,
    PublicationVersionSpec,
)


def load(col: Collector) -> None:
    col.adds(
        [
            PublicationPackageZipSpec(
                key="publication_package_zip_1",
                file_path="package-1",
            ),
        ]
    )

    zip_ref = col.ref(PublicationPackageZipSpec, "publication_package_zip_1")
    col.adds(
        [
            PublicationActPackageSpec(
                key="act_package_visie_validation",
                publication_version_id=col.ref(PublicationVersionSpec, "publication_version_module_1_visie"),
                module_id=col.ref(ModuleSpec, "module_1"),
                module_status_id=col.ref(ModuleStatusHistorySpec, "module_1_status_ter_inzage"),
                zip_id=zip_ref,
                package_type="validation",
                report_status="valid",
                created_date=datetime(2025, 7, 1, tzinfo=UTC),
                modified_date=datetime(2025, 7, 1, tzinfo=UTC),
            ),
            PublicationActPackageSpec(
                key="act_package_visie_publication",
                publication_version_id=col.ref(PublicationVersionSpec, "publication_version_module_1_visie"),
                module_id=col.ref(ModuleSpec, "module_1"),
                module_status_id=col.ref(ModuleStatusHistorySpec, "module_1_status_ter_inzage"),
                zip_id=zip_ref,
                package_type="publication",
                report_status="valid",
                created_date=datetime(2025, 7, 2, tzinfo=UTC),
                modified_date=datetime(2025, 7, 2, tzinfo=UTC),
            ),
            PublicationActPackageSpec(
                key="act_package_programma_validation",
                publication_version_id=col.ref(PublicationVersionSpec, "publication_version_module_4_programma"),
                module_id=col.ref(ModuleSpec, "module_4"),
                module_status_id=col.ref(ModuleStatusHistorySpec, "module_4_status_ontwerp_gs_concept"),
                zip_id=zip_ref,
                package_type="validation",
                report_status="failed",
                created_date=datetime(2025, 7, 3, tzinfo=UTC),
                modified_date=datetime(2025, 7, 3, tzinfo=UTC),
            ),
            PublicationAnnouncementSpec(
                key="announcement_visie",
                act_package_id=col.ref(PublicationActPackageSpec, "act_package_visie_publication"),
                publication_id=col.ref(PublicationSpec, "publication_module_1_visie"),
            ),
            PublicationAnnouncementPackageSpec(
                key="announcement_package_visie_publication",
                announcement_id=col.ref(PublicationAnnouncementSpec, "announcement_visie"),
                zip_id=zip_ref,
                package_type="publication",
                report_status="pending",
                created_date=datetime(2025, 7, 4, tzinfo=UTC),
                modified_date=datetime(2025, 7, 4, tzinfo=UTC),
            ),
        ]
    )
