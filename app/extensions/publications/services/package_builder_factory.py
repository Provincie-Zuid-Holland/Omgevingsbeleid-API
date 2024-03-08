from sqlalchemy.orm import Session

from app.extensions.publications.enums import PackageType
from app.extensions.publications.services.act_frbr_provider import ActFrbrProvider
from app.extensions.publications.services.bill_frbr_provider import BillFrbrProvider
from app.extensions.publications.services.package_builder import PackageBuilder
from app.extensions.publications.services.publication_data_provider import PublicationDataProvider
from app.extensions.publications.tables.tables import PublicationVersionTable


class PackageBuilderFactory:
    def __init__(
        self,
        db: Session,
        bill_frbr_provider: BillFrbrProvider,
        act_frbr_provider: ActFrbrProvider,
        publication_data_provider: PublicationDataProvider,
    ):
        self._db: Session = db
        self._bill_frbr_provider: BillFrbrProvider = bill_frbr_provider
        self._act_frbr_provider: ActFrbrProvider = act_frbr_provider
        self._publication_data_provider: PublicationDataProvider = publication_data_provider

    def create_builder(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
    ) -> PackageBuilder:
        builder: PackageBuilder = PackageBuilder(
            self._db,
            self._bill_frbr_provider,
            self._act_frbr_provider,
            self._publication_data_provider,
            publication_version,
            package_type,
        )
        return builder
