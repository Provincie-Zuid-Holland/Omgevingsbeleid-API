from typing import Optional

from dso.act_builder.state_manager.input_data.input_data_loader import InputData
from sqlalchemy.orm import Session

from app.api.domains.publications.exceptions import DSOConfigurationException
from app.api.domains.publications.services.act_frbr_provider import ActFrbrProvider
from app.api.domains.publications.services.act_package.act_package_builder import ActPackageBuilder
from app.api.domains.publications.services.act_package.act_publication_data_provider import ActPublicationDataProvider
from app.api.domains.publications.services.act_package.api_act_input_data_patcher import ApiActInputDataPatcher
from app.api.domains.publications.services.act_package.api_act_input_data_patcher_factory import (
    ApiActInputDataPatcherFactory,
)
from app.api.domains.publications.services.act_package.dso_act_input_data_builder import DsoActInputDataBuilder
from app.api.domains.publications.services.act_package.dso_act_input_data_builder_factory import (
    DsoActInputDataBuilderFactory,
)
from app.api.domains.publications.services.bill_frbr_provider import BillFrbrProvider
from app.api.domains.publications.services.purpose_provider import PurposeProvider
from app.api.domains.publications.services.state.state_loader import StateLoader
from app.api.domains.publications.services.state.versions import ActiveState
from app.api.domains.publications.services.validate_publication_service import (
    ValidatePublicationService,
    ValidatePublicationException,
    ValidatePublicationRequest,
)
from app.api.domains.publications.types.api_input_data import (
    ActFrbr,
    ApiActInputData,
    BillFrbr,
    PublicationData,
    Purpose,
)
from app.api.domains.publications.types.enums import MutationStrategy, PackageType, PurposeType
from app.core.tables.publications import PublicationActTable, PublicationTable, PublicationVersionTable


class ActPackageBuilderFactory:
    def __init__(
        self,
        dso_builder_factory: DsoActInputDataBuilderFactory,
        bill_frbr_provider: BillFrbrProvider,
        act_frbr_provider: ActFrbrProvider,
        purpose_provider: PurposeProvider,
        state_loader: StateLoader,
        publication_data_provider: ActPublicationDataProvider,
        data_patcher_factory: ApiActInputDataPatcherFactory,
        validate_publication_service: ValidatePublicationService,
    ):
        self._dso_builder_factory: DsoActInputDataBuilderFactory = dso_builder_factory
        self._bill_frbr_provider: BillFrbrProvider = bill_frbr_provider
        self._act_frbr_provider: ActFrbrProvider = act_frbr_provider
        self._purpose_provider: PurposeProvider = purpose_provider
        self._state_loader: StateLoader = state_loader
        self._publication_data_provider: ActPublicationDataProvider = publication_data_provider
        self._data_patcher_factory: ApiActInputDataPatcherFactory = data_patcher_factory
        self._validate_publication_service: ValidatePublicationService = validate_publication_service

    def create_builder(
        self,
        session: Session,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
        mutation_strategy: MutationStrategy,
    ) -> ActPackageBuilder:
        publication: PublicationTable = publication_version.Publication
        act: PublicationActTable = publication.Act

        act_frbr: ActFrbr = self._act_frbr_provider.generate_frbr(session, act)
        bill_frbr: BillFrbr = self._bill_frbr_provider.generate_frbr(session, publication.Environment, act_frbr)
        purpose: Purpose = self._purpose_provider.generate_purpose(
            publication_version,
            act_frbr,
            PurposeType.CONSOLIDATION,
        )
        publication_data: PublicationData = self._publication_data_provider.fetch_data(
            session,
            publication_version,
            bill_frbr,
            act_frbr,
        )

        api_input_data = ApiActInputData(
            Bill_Frbr=bill_frbr,
            Act_Frbr=act_frbr,
            Consolidation_Purpose=purpose,
            Publication_Data=publication_data,
            Package_Type=package_type,
            Publication_Version=publication_version,
            Act_Mutation=None,
            Ow_State=None,
            Mutation_Strategy=mutation_strategy,
        )

        state: Optional[ActiveState] = self._state_loader.load_from_publication_version(session, publication_version)
        if state is not None:
            data_patcher: ApiActInputDataPatcher = self._data_patcher_factory.create(state)
            api_input_data = data_patcher.apply(session, api_input_data)

        validation_request = ValidatePublicationRequest(
            document_type=publication_version.Publication.Document_Type,
            module_id=publication_version.Publication.Module_ID,
            input_data=api_input_data,
        )
        validation_result = self._validate_publication_service.validate(session, validation_request)
        if len(validation_result.errors) > 0:
            raise ValidatePublicationException(
                "Error(s) found while validating publication",
                publication_errors=validation_result.errors,
            )

        input_data_builder: DsoActInputDataBuilder = self._dso_builder_factory.create(
            api_input_data,
        )

        try:
            input_data: InputData = input_data_builder.build()
        except Exception as e:
            raise DSOConfigurationException(str(e)) from e

        builder: ActPackageBuilder = ActPackageBuilder(
            api_input_data,
            state,
            input_data,
        )
        return builder
