from sqlalchemy.orm import Session

from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.builder import Builder

from app.extensions.publications.enums import PackageType
from app.extensions.publications.services.act_frbr_provider import ActFrbr, ActFrbrProvider
from app.extensions.publications.services.bill_frbr_provider import BillFrbr, BillFrbrProvider
from app.extensions.publications.services.dso_input_data_builder import DsoInputDataBuilder
from app.extensions.publications.services.publication_data_provider import PublicationData, PublicationDataProvider
from app.extensions.publications.tables.tables import PublicationVersionTable


class PackageBuilder:
    def __init__(
        self,
        db: Session,
        bill_frbr_provider: BillFrbrProvider,
        act_frbr_provider: ActFrbrProvider,
        publication_data_provider: PublicationDataProvider,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
    ):
        self._db: Session = db
        self._bill_frbr_provider: BillFrbrProvider = bill_frbr_provider
        self._act_frbr_provider: ActFrbrProvider = act_frbr_provider
        self._publication_data_provider: PublicationDataProvider = publication_data_provider
        self._publication_version: PublicationVersionTable = publication_version
        self._package_type: PackageType = package_type

    def build(self) -> Builder:
        bill_frbr: BillFrbr = self._bill_frbr_provider.generate_frbr(
            self._publication_version,
            self._package_type,
        )
        act_frbr: ActFrbr = self._act_frbr_provider.generate_frbr(
            self._publication_version,
            self._package_type,
        )
        publication_data: PublicationData = self._publication_data_provider.fetch_data(
            self._publication_version,
        )

        # @todo: transform data based on state
        #           this includes adding "Intrekkingen" if needed

        input_data: InputData = self._build_dso_input(
            bill_frbr,
            act_frbr,
            publication_data,
        )

        builder: Builder = Builder(input_data)
        return builder
    
    def _build_dso_input(
        self,
        bill_frbr: BillFrbr,
        act_frbr: ActFrbr,
        publication_data: PublicationData,
    ) -> InputData:
        input_data_builder: DsoInputDataBuilder = DsoInputDataBuilder(
            self._publication_version,
            self._package_type,
            bill_frbr,
            act_frbr,
            publication_data,
        )
        input_data: InputData = input_data_builder.build()
        return input_data
