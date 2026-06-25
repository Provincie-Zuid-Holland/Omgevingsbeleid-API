from datetime import datetime, timezone

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    col.adds(
        [
            StorageFileSpec(
                key="document_1",
                File_Path="./document-1.pdf",
                Created_Date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            ),
            StorageFileSpec(
                key="document_2",
                File_Path="./document-2.pdf",
                Created_Date=datetime(2025, 1, 2, tzinfo=timezone.utc),
                Created_By_UUID=col.ref(UserSpec, "ambtenaar"),
            ),
            StorageFileSpec(
                key="document_3",
                File_Path="./document-3.pdf",
                Created_Date=datetime(2025, 1, 3, tzinfo=timezone.utc),
            ),
        ]
    )
