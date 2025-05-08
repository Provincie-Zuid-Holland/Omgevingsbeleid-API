from typing import Optional

from fastapi import HTTPException, status

from app.api.domains.objects.types import FilterObjectCode


def depends_filter_object_code(
    object_type: Optional[str] = None,
    lineage_id: Optional[int] = None,
) -> Optional[FilterObjectCode]:
    if object_type is None and lineage_id is None:
        return None

    if object_type is None or lineage_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "object_type and object_lineage_id should be supplied together."
        )

    return FilterObjectCode(
        object_type=object_type,
        lineage_id=lineage_id,
    )
