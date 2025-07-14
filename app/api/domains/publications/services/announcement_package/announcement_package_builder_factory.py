from typing import Optional

from dso.announcement_builder.state_manager.models import InputData
from sqlalchemy.orm import Session

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

    def create_builder(
        self,
        session: Session,
        announcement: PublicationAnnouncementTable,
        package_type: PackageType,
    ) -> AnnouncementPackageBuilder:
        doc_frbr: DocFrbr = self._doc_frbr_provider.generate_frbr(session, announcement)
        about_act_frbr: ActFrbr = self._get_about_act_frbr(announcement)
        about_bill_frbr: BillFrbr = self._get_about_bill_frbr(announcement)

        api_input_data = ApiAnnouncementInputData(
            Doc_Frbr=doc_frbr,
            About_Bill_Frbr=about_bill_frbr,
            About_Act_Frbr=about_act_frbr,
            Package_Type=package_type,
            Announcement=announcement,
            Announcement_Metadata=AnnouncementMetadata.model_validate(announcement.Metadata),
            Announcement_Procedural=AnnouncementProcedural.model_validate(announcement.Procedural),
            Announcement_Content=AnnouncementContent.model_validate(announcement.Content),
        )

        state: Optional[ActiveState] = self._state_loader.load_from_environment(
            session, announcement.Publication.Environment
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
        bill_version_table: PublicationBillVersionTable = announcement.Act_Package.Bill_Version

        result = BillFrbr(
            Work_Province_ID=bill_version_table.Bill.Work_Province_ID,
            Work_Country=bill_version_table.Bill.Work_Country,
            Work_Date=bill_version_table.Bill.Work_Date,
            Work_Other=bill_version_table.Bill.Work_Other,
            Expression_Language=bill_version_table.Expression_Language,
            Expression_Date=bill_version_table.Expression_Date,
            Expression_Version=bill_version_table.Expression_Version,
        )
        return result

    def _get_about_act_frbr(self, announcement: PublicationAnnouncementTable) -> ActFrbr:
        act_version_table: PublicationActVersionTable = announcement.Act_Package.Act_Version

        result = ActFrbr(
            Act_ID=act_version_table.Act.ID,
            Work_Province_ID=act_version_table.Act.Work_Province_ID,
            Work_Country=act_version_table.Act.Work_Country,
            Work_Date=act_version_table.Act.Work_Date,
            Work_Other=act_version_table.Act.Work_Other,
            Expression_Language=act_version_table.Expression_Language,
            Expression_Date=act_version_table.Expression_Date,
            Expression_Version=act_version_table.Expression_Version,
        )
        return result
