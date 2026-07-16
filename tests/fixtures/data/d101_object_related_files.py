from datetime import datetime, timezone

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.object_related_file_spec import ObjectRelatedFileSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_By_UUID=col.ref(UserSpec, "ambtenaar"),
    ):
        # Files for beleidsdoel-1
        col.adds(
            [
                ObjectRelatedFileSpec(
                    key="bd1_file1",
                    Code="beleidsdoel-1",
                    Title="Document 1 for beleidsdoel 1",
                    File_Ref=col.ref(StorageFileSpec, "file_1"),
                    Created_Date=datetime(2025, 4, 1, tzinfo=timezone.utc),
                ),
                ObjectRelatedFileSpec(
                    key="bd1_file2",
                    Code="beleidsdoel-1",
                    Title="Document 2 for beleidsdoel 1",
                    File_Ref=col.ref(StorageFileSpec, "file_2"),
                    Created_Date=datetime(2025, 4, 2, tzinfo=timezone.utc),
                ),
            ]
        )

        # Files for beleidsdoel-2
        col.add(
            ObjectRelatedFileSpec(
                key="bd2_file1",
                Code="beleidsdoel-2",
                Title="Document 1 for beleidsdoel 2",
                File_Ref=col.ref(StorageFileSpec, "file_1"),
                Created_Date=datetime(2025, 4, 1, tzinfo=timezone.utc),
            )
        )
