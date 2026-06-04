from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec


def load(col: Collector) -> None:
    col.adds(
        [
            StorageFileSpec(
                File_Path="./document-1.pdf",
            ),
            StorageFileSpec(
                File_Path="./document-2.pdf",
            ),
            StorageFileSpec(
                File_Path="./document-3.pdf",
            ),
        ]
    )
