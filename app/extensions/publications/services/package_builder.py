import hashlib
import io
from dataclasses import dataclass

from dso.builder.builder import Builder
from dso.builder.state_manager.input_data.input_data_loader import InputData


@dataclass
class ZipData:
    Publication_Filename: str
    Filename: str
    Binary: bytes
    Checksum: str


class PackageBuilder:
    def __init__(
        self,
        input_data: InputData,
    ):
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

    def get_delivery_id(self) -> str:
        delivery_id: str = self._input_data.publication_settings.opdracht.id_levering
        return delivery_id
