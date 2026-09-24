from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    col.adds(
        [
            StorageFileSpec(
                key="file_1",
                file_path="./document-1.pdf",
                created_date=datetime(2025, 1, 1, tzinfo=UTC),
            ),
            StorageFileSpec(
                key="file_2",
                file_path="./document-2.pdf",
                created_date=datetime(2025, 1, 2, tzinfo=UTC),
                created_by_id=col.ref(UserSpec, "ambtenaar"),
            ),
            StorageFileSpec(
                key="file_3",
                file_path="./document-3.pdf",
                created_date=datetime(2025, 1, 3, tzinfo=UTC),
            ),
        ]
    )
