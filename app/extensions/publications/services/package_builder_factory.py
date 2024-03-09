from dso.builder.state_manager.input_data.input_data_loader import InputData
from sqlalchemy.orm import Session

from app.extensions.publications.enums import PackageType
from app.extensions.publications.services.act_frbr_provider import ActFrbr, ActFrbrProvider
from app.extensions.publications.services.bill_frbr_provider import BillFrbr, BillFrbrProvider
from app.extensions.publications.services.dso_input_data_builder import DsoInputDataBuilder
from app.extensions.publications.services.package_builder import PackageBuilder
from app.extensions.publications.services.publication_data_provider import PublicationData, PublicationDataProvider
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
        bill_frbr: BillFrbr = self._bill_frbr_provider.generate_frbr(
            publication_version,
            package_type,
        )
        act_frbr: ActFrbr = self._act_frbr_provider.generate_frbr(
            publication_version,
            package_type,
        )
        publication_data: PublicationData = self._publication_data_provider.fetch_data(
            publication_version,
        )

        # @todo: transform data based on state
        #           this includes adding "Intrekkingen" if needed

        input_data_builder: DsoInputDataBuilder = DsoInputDataBuilder(
            publication_version,
            package_type,
            bill_frbr,
            act_frbr,
            publication_data,
        )
        input_data: InputData = input_data_builder.build()

        builder: PackageBuilder = PackageBuilder(input_data)
        return builder
