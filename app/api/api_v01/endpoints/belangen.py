from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDBelang
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {"Omschrijving"}


@router.get(
    "/belangen",
    response_model=List[schemas.Belang],
    response_model_exclude=defer_attributes,
)
def read_belangen(
    crud_belang: CRUDBelang = Depends(deps.get_crud_belang),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = -1,
) -> Any:
    """
    Gets all the belangen lineages and shows the latests object for each
    """
    belangen = crud_belang.latest(all=True, filters=filters, offset=offset, limit=limit)

    return belangen


@router.post("/belangen", response_model=schemas.Belang)
def create_belang(
    *,
    belang_in: schemas.BelangCreate,
    crud_belang: CRUDBelang = Depends(deps.get_crud_belang),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new belangen lineage
    """
    belang = crud_belang.create(obj_in=belang_in, by_uuid=current_gebruiker.UUID)
    return belang


@router.get("/belangen/{lineage_id}", response_model=List[schemas.Belang])
def read_belang_lineage(
    *,
    lineage_id: int,
    crud_belang: CRUDBelang = Depends(deps.get_crud_belang),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the belangen versions by lineage
    """
    belangen = crud_belang.all(filters=Filters({"ID": lineage_id}))
    if not belangen:
        raise HTTPException(status_code=404, detail="Belangs not found")
    return belangen


@router.patch("/belangen/{lineage_id}", response_model=schemas.Belang)
def update_belang(
    *,
    lineage_id: int,
    belang_in: schemas.BelangUpdate,
    crud_belang: CRUDBelang = Depends(deps.get_crud_belang),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new belangen to a lineage
    """
    belang = crud_belang.get_latest_by_id(id=lineage_id)
    if not belang:
        raise HTTPException(status_code=404, detail="Belang not found")
    if belang.Created_By.UUID != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    belang = crud_belang.update(
        db_obj=belang, obj_in=belang_in, by_uuid=str(current_gebruiker.UUID)
    )
    return belang


@router.get("/changes/belangen/{old_uuid}/{new_uuid}")
def changes_belangen(
    old_uuid: str,
    new_uuid: str,
    crud_belang: CRUDBelang = Depends(deps.get_crud_belang),
) -> Any:
    """
    Shows the changes between two versions of belangen.
    """
    try:
        old = crud_belang.get(old_uuid)
        new = crud_belang.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )
    json_data = Comparator(schema=schemas.Belang, old=old, new=new).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/belangen",
    response_model=List[schemas.Belang],
    response_model_exclude=defer_attributes,
)
def read_valid_belangen(
    crud_belang: CRUDBelang = Depends(deps.get_crud_belang),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = -1,
) -> Any:
    """
    Gets all the belangen lineages and shows the latests valid object for each.
    """
    belangen = crud_belang.valid(offset=offset, limit=limit, filters=filters)
    return belangen


@router.get("/valid/belangen/{lineage_id}", response_model=List[schemas.Belang])
def read_valid_belang_lineage(
    lineage_id: int,
    filters: Filters = Depends(deps.string_filters),
    crud_belang: CRUDBelang = Depends(deps.get_crud_belang),
    offset: int = 0,
    limit: int = -1,
) -> Any:
    """
    Gets all the belangen in this lineage that are valid
    """
    belangen = crud_belang.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not belangen:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return belangen


@router.get(
    "/version/belangen/{object_uuid}",
    response_model=schemas.Belang,
    operation_id="read_belang_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_belang: CRUDBelang = Depends(deps.get_crud_belang),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    belang = crud_belang.get_latest_by_uuid(uuid=object_uuid)

    if not belang:
        raise HTTPException(status_code=404, detail="Belangen lineage not found")

    return belang
