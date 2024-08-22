from typing import Optional

from dso.act_builder.state_manager.input_data.input_data_loader import InputData
from sqlalchemy.orm import Session

from app.core.settings.dynamic_settings import DynamicSettings
from app.extensions.publications.enums import PackageType, PurposeType
from app.extensions.publications.exceptions import DSOConfigurationException
from app.extensions.publications.models.api_input_data import ApiActInputData, OwData, PublicationData, Purpose
from app.extensions.publications.services.act_frbr_provider import ActFrbr, ActFrbrProvider
from app.extensions.publications.services.act_package.act_package_builder import ActPackageBuilder
from app.extensions.publications.services.act_package.act_publication_data_provider import ActPublicationDataProvider
from app.extensions.publications.services.act_package.api_act_input_data_patcher import ApiActInputDataPatcher
from app.extensions.publications.services.act_package.dso_act_input_data_builder import DsoActInputDataBuilder
from app.extensions.publications.services.bill_frbr_provider import BillFrbr, BillFrbrProvider
from app.extensions.publications.services.purpose_provider import PurposeProvider
from app.extensions.publications.services.state.state_loader import StateLoader
from app.extensions.publications.services.state.versions import ActiveState
from app.extensions.publications.tables.tables import PublicationActTable, PublicationTable, PublicationVersionTable


class ActPackageBuilderFactory:
    def __init__(
        self,
        db: Session,
        settings: DynamicSettings,
        bill_frbr_provider: BillFrbrProvider,
        act_frbr_provider: ActFrbrProvider,
        purpose_provider: PurposeProvider,
        state_loader: StateLoader,
        publication_data_provider: ActPublicationDataProvider,
    ):
        self._db: Session = db
        self._settings: DynamicSettings = settings
        self._bill_frbr_provider: BillFrbrProvider = bill_frbr_provider
        self._act_frbr_provider: ActFrbrProvider = act_frbr_provider
        self._purpose_provider: PurposeProvider = purpose_provider
        self._state_loader: StateLoader = state_loader
        self._publication_data_provider: ActPublicationDataProvider = publication_data_provider

    def create_builder(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
    ) -> ActPackageBuilder:
        publication: PublicationTable = publication_version.Publication
        act: PublicationActTable = publication.Act

        bill_frbr: BillFrbr = self._bill_frbr_provider.generate_frbr(publication_version)
        act_frbr: ActFrbr = self._act_frbr_provider.generate_frbr(act)
        purpose: Purpose = self._purpose_provider.generate_purpose(
            publication_version,
            act_frbr,
            PurposeType.CONSOLIDATION,
        )
        publication_data: PublicationData = self._publication_data_provider.fetch_data(
            publication_version,
            bill_frbr,
            act_frbr,
        )

        api_input_data: ApiActInputData = ApiActInputData(
            Bill_Frbr=bill_frbr,
            Act_Frbr=act_frbr,
            Consolidation_Purpose=purpose,
            Publication_Data=publication_data,
            Package_Type=package_type,
            Publication_Version=publication_version,
            Act_Mutation=None,
            Ow_Data=OwData(),
        )

        state: Optional[ActiveState] = self._state_loader.load_from_publication_version(publication_version)
        if state is not None:
            data_patcher: ApiActInputDataPatcher = ApiActInputDataPatcher(state)
            api_input_data = data_patcher.apply(api_input_data)

        input_data_builder: DsoActInputDataBuilder = DsoActInputDataBuilder(
            self._settings,
            api_input_data,
        )

        try:
            input_data: InputData = input_data_builder.build()
        except Exception as e:
            raise DSOConfigurationException(str(e))

        builder: ActPackageBuilder = ActPackageBuilder(
            api_input_data,
            state,
            input_data,
        )
        return builder
