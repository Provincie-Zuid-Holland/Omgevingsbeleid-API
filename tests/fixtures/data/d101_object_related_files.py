from datetime import datetime, timezone

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.object_related_file_spec import ObjectRelatedFileSpec
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_Date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        Created_By_UUID=col.ref(UserSpec, "ambtenaar"),
    ):
        # Files for beleidsdoel-1
        col.adds(
            [
                ObjectRelatedFileSpec(
                    Code="beleidsdoel-1",
                    Title="Document 1 for beleidsdoel 1",
                    File_Ref=col.ref(StorageFileSpec, "document_1"),
                ),
                ObjectRelatedFileSpec(
                    Code="beleidsdoel-2",
                    Title="Document 2 for beleidsdoel 1",
                    File_Ref=col.ref(StorageFileSpec, "document_2"),
                ),
            ]
        )

        # Files for beleidsdoel-2
        col.add(
            ObjectRelatedFileSpec(
                Code="beleidsdoel-2",
                Title="Document 1 for beleidsdoel 2",
                File_Ref=col.ref(StorageFileSpec, "document_1"),
            )
        )
