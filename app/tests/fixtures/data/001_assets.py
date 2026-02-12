from datetime import datetime
from typing import List

from app.core.tables.others import StorageFileTable
from app.tests.fixtures.types import FixtureContext, StorageFileFactory


def fixtures(_: FixtureContext) -> List[StorageFileTable]:
    base_path = "./app/tests/fixtures/files/"
    created_date = datetime(2022, 2, 2, 3, 3, 3)
    return [
        StorageFileFactory(id=1, file_path=f"{base_path}document-1.pdf", created_date=created_date).create(),
        StorageFileFactory(id=2, file_path=f"{base_path}document-2.pdf", created_date=created_date).create(),
    ]
