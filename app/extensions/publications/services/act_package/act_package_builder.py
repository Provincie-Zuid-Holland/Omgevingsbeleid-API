import hashlib
import io
import uuid
from typing import Optional

from dso.act_builder.builder import Builder
from dso.act_builder.state_manager.input_data.input_data_loader import InputData

from app.extensions.publications.models.api_input_data import ApiActInputData, Purpose
from app.extensions.publications.models.zip import ZipData
from app.extensions.publications.services.act_frbr_provider import ActFrbr
from app.extensions.publications.services.act_package.act_state_patcher import ActStatePatcher
from app.extensions.publications.services.bill_frbr_provider import BillFrbr
from app.extensions.publications.services.state.state import State
from app.extensions.publications.services.state.versions import ActiveState
from app.extensions.publications.tables.tables import PublicationEnvironmentStateTable, PublicationEnvironmentTable


class ActPackageBuilder:
    def __init__(
        self,
        api_input_data: ApiActInputData,
        state: Optional[ActiveState],
        input_data: InputData,
    ):
        self._api_input_data: ApiActInputData = api_input_data
        self._state: Optional[ActiveState] = state
        self._input_data: InputData = input_data
        self._dso_builder: Builder = Builder(input_data)

    def build_publication_files(self):
        self._dso_builder.build_publication_files()

    def save_files(self, output_dir: str):
        self._dso_builder.save_files(output_dir)

    def zip_files(self) -> ZipData:
        zip_buffer: io.BytesIO = self._dso_builder.zip_files()
        zip_content: bytes = zip_buffer.getvalue()
        publication_filename: str = self._input_data.publication_settings.opdracht.publicatie_bestand
        filename: str = publication_filename.replace(".xml", ".zip")
        checksum: str = hashlib.sha256(zip_content).hexdigest()
        zip_data: ZipData = ZipData(
            Publication_Filename=publication_filename,
            Filename=filename,
            Binary=zip_content,
            Checksum=checksum,
        )
        return zip_data

    def get_input_data(self) -> InputData:
        return self._input_data

    def get_delivery_id(self) -> str:
        delivery_id: str = self._input_data.publication_settings.opdracht.id_levering
        return delivery_id

    def get_bill_frbr(self) -> BillFrbr:
        return self._api_input_data.Bill_Frbr

    def get_act_frbr(self) -> ActFrbr:
        return self._api_input_data.Act_Frbr

    def get_consolidation_purpose(self) -> Purpose:
        return self._api_input_data.Consolidation_Purpose

    def create_new_state(self) -> Optional[PublicationEnvironmentStateTable]:
        if self._state is None:
            raise RuntimeError("Can not create new state")

        environment: PublicationEnvironmentTable = self._api_input_data.Publication_Version.Publication.Environment

        state_changer: ActStatePatcher = ActStatePatcher(self._api_input_data, self._dso_builder)
        state: State = state_changer.apply(self._state)

        state_table: PublicationEnvironmentStateTable = PublicationEnvironmentStateTable(
            UUID=uuid.uuid4(),
            Environment_UUID=environment.UUID,
            Adjust_On_UUID=environment.Active_State_UUID,
            State=state.state_dict(),
            Is_Activated=False,
            Activated_Datetime=None,
        )
        return state_table
