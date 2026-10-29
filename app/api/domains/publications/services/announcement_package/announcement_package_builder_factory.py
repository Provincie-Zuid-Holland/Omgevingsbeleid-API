from dso.announcement_builder.state_manager.models import InputData
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.announcement_package.announcement_package_builder import (
    AnnouncementPackageBuilder,
)
from app.api.domains.publications.services.announcement_package.dso_announcement_input_data_builder import (
    DsoAnnouncementInputDataBuilder,
)
from app.api.domains.publications.services.doc_frbr_provider import DocFrbrProvider
from app.api.domains.publications.services.state.state_loader import StateLoader
from app.api.domains.publications.services.state.versions import ActiveState
from app.api.domains.publications.types.api_input_data import ActFrbr, ApiAnnouncementInputData, BillFrbr, DocFrbr
from app.api.domains.publications.types.enums import PackageType
from app.api.domains.publications.types.models import AnnouncementContent, AnnouncementMetadata, AnnouncementProcedural
from app.core.tables.publications import (
    PublicationActVersionTable,
    PublicationAnnouncementTable,
    PublicationBillVersionTable,
)


class AnnouncementPackageBuilderFactory:
    def __init__(
        self,
        doc_frbr_provider: DocFrbrProvider,
        state_loader: StateLoader,
    ):
        self._doc_frbr_provider: DocFrbrProvider = doc_frbr_provider
        self._state_loader: StateLoader = state_loader

    async def create_builder(
        self,
        session: AsyncSession,
        announcement: PublicationAnnouncementTable,
        package_type: PackageType,
    ) -> AnnouncementPackageBuilder:
        doc_frbr: DocFrbr = await self._doc_frbr_provider.generate_frbr(session, announcement)
        about_act_frbr: ActFrbr = self._get_about_act_frbr(announcement)
        about_bill_frbr: BillFrbr = self._get_about_bill_frbr(announcement)

        api_input_data = ApiAnnouncementInputData(
            doc_frbr=doc_frbr,
            about_bill_frbr=about_bill_frbr,
            about_act_frbr=about_act_frbr,
            package_type=package_type,
            announcement=announcement,
            announcement_metadata=AnnouncementMetadata.model_validate(announcement.meta_data),
            announcement_procedural=AnnouncementProcedural.model_validate(announcement.procedural),
            announcement_content=AnnouncementContent.model_validate(announcement.content),
        )

        state: ActiveState | None = await self._state_loader.load_from_environment(
            session, announcement.publication.environment
        )

        input_data_builder = DsoAnnouncementInputDataBuilder(api_input_data)
        input_data: InputData = input_data_builder.build()

        builder: AnnouncementPackageBuilder = AnnouncementPackageBuilder(
            api_input_data,
            state,
            input_data,
        )
        return builder

    def _get_about_bill_frbr(self, announcement: PublicationAnnouncementTable) -> BillFrbr:
        bill_version_table: PublicationBillVersionTable = announcement.act_package.bill_version

        result = BillFrbr(
            work_province_id=bill_version_table.bill.work_province_id,
            work_country=bill_version_table.bill.work_country,
            work_date=bill_version_table.bill.work_date,
            work_other=bill_version_table.bill.work_other,
            expression_language=bill_version_table.expression_language,
            expression_date=bill_version_table.expression_date,
            expression_version=bill_version_table.expression_version,
        )
        return result

    def _get_about_act_frbr(self, announcement: PublicationAnnouncementTable) -> ActFrbr:
        act_version_table: PublicationActVersionTable = announcement.act_package.act_version

        result = ActFrbr(
            act_id=act_version_table.act.id,
            work_province_id=act_version_table.act.work_province_id,
            work_country=act_version_table.act.work_country,
            work_date=act_version_table.act.work_date,
            work_other=act_version_table.act.work_other,
            expression_language=act_version_table.expression_language,
            expression_date=act_version_table.expression_date,
            expression_version=act_version_table.expression_version,
        )
        return result
