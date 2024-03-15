from typing import Optional

from dso.builder.state_manager.input_data.input_data_loader import InputData
from sqlalchemy.orm import Session

from app.extensions.publications.enums import PackageType
from app.extensions.publications.models.api_input_data import ApiInputData, PublicationData
from app.extensions.publications.services.act_frbr_provider import ActFrbr, ActFrbrProvider
from app.extensions.publications.services.bill_frbr_provider import BillFrbr, BillFrbrProvider
from app.extensions.publications.services.dso_input_data_builder import DsoInputDataBuilder
from app.extensions.publications.services.package_builder import PackageBuilder
from app.extensions.publications.services.publication_data_provider import PublicationDataProvider
from app.extensions.publications.services.state.state import State
from app.extensions.publications.services.state.state_loader import StateLoader
from app.extensions.publications.tables.tables import PublicationVersionTable


class PackageBuilderFactory:
    def __init__(
        self,
        db: Session,
        bill_frbr_provider: BillFrbrProvider,
        act_frbr_provider: ActFrbrProvider,
        state_loader: StateLoader,
        publication_data_provider: PublicationDataProvider,
    ):
        self._db: Session = db
        self._bill_frbr_provider: BillFrbrProvider = bill_frbr_provider
        self._act_frbr_provider: ActFrbrProvider = act_frbr_provider
        self._state_loader: StateLoader = state_loader
        self._publication_data_provider: PublicationDataProvider = publication_data_provider

    def create_builder(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
    ) -> PackageBuilder:
        bill_frbr: BillFrbr = self._bill_frbr_provider.generate_frbr(publication_version)
        act_frbr: ActFrbr = self._act_frbr_provider.generate_frbr(publication_version)
        publication_data: PublicationData = self._publication_data_provider.fetch_data(
            publication_version,
            act_frbr,
        )

        api_input_data: ApiInputData = ApiInputData(
            Bill_Frbr=bill_frbr,
            Act_Frbr=act_frbr,
            Publication_Data=publication_data,
            Package_Type=package_type,
            Publication_Version=publication_version,
        )

        state: Optional[State] = self._state_loader.load_from_publication_version(publication_version)
        # @todo: transform data based on state
        # @todo: this includes adding "Intrekkingen" if needed

        input_data_builder: DsoInputDataBuilder = DsoInputDataBuilder(
            api_input_data,
        )
        input_data: InputData = input_data_builder.build()

        builder: PackageBuilder = PackageBuilder(
            api_input_data,
            state,
            input_data,
        )
        return builder
