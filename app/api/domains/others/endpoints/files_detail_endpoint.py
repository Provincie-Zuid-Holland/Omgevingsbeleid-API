from typing import Annotated

from fastapi import Depends

from app.api.domains.others.dependencies import depends_storage_file
from app.api.domains.others.types import StorageFileBasic
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.others import StorageFileTable
from app.core.tables.users import UsersTable


def get_files_detail_endpoint(
    storage_file: Annotated[StorageFileTable, Depends(depends_storage_file)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
) -> StorageFileBasic:
    result: StorageFileBasic = StorageFileBasic.model_validate(storage_file)
    return result
