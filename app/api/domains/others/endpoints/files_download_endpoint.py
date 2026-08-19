from typing import Annotated

from fastapi import Depends, Response

from app.api.domains.others.dependencies import depends_storage_file
from app.core.tables.others import StorageFileTable


def get_files_download_endpoint(
    storage_file: Annotated[StorageFileTable, Depends(depends_storage_file)],
) -> Response:
    filename = storage_file.Filename
    content = storage_file.Binary
    content_type = storage_file.Content_Type

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(content)),
        },
    )
