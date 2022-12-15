from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDThema
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {"Omschrijving"}


@router.get(
    "/themas",
    response_model=List[schemas.Thema],
    response_model_exclude=defer_attributes,
)
def read_themas(
    crud_thema: CRUDThema = Depends(deps.get_crud_thema),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the themas lineages and shows the latests object for each
    """
    themas = crud_thema.latest(all=True, filters=filters, offset=offset, limit=limit)

    return themas


@router.post("/themas", response_model=schemas.Thema)
def create_thema(
    *,
    thema_in: schemas.ThemaCreate,
    crud_thema: CRUDThema = Depends(deps.get_crud_thema),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new themas lineage
    """
    thema = crud_thema.create(obj_in=thema_in, by_uuid=current_gebruiker.UUID)
    return thema


@router.get("/themas/{lineage_id}", response_model=List[schemas.Thema])
def read_thema_lineage(
    *,
    lineage_id: int,
    crud_thema: CRUDThema = Depends(deps.get_crud_thema),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the themas versions by lineage
    """
    themas = crud_thema.all(filters=Filters({"ID": lineage_id}))
    if not themas:
        raise HTTPException(status_code=404, detail="Themas not found")
    return themas


@router.patch("/themas/{lineage_id}", response_model=schemas.Thema)
def update_thema(
    *,
    lineage_id: int,
    thema_in: schemas.ThemaUpdate,
    crud_thema: CRUDThema = Depends(deps.get_crud_thema),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new themas to a lineage
    """
    thema = crud_thema.get_latest_by_id(id=lineage_id)
    if not thema:
        raise HTTPException(status_code=404, detail="Thema not found")
    if thema.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    thema = crud_thema.update(
        db_obj=thema, obj_in=thema_in, by_uuid=str(current_gebruiker.UUID)
    )
    return thema


@router.get("/changes/themas/{old_uuid}/{new_uuid}")
def changes_themas(
    old_uuid: str,
    new_uuid: str,
    crud_thema: CRUDThema = Depends(deps.get_crud_thema),
) -> Any:
    """
    Shows the changes between two versions of themas.
    """
    try:
        old = crud_thema.get(old_uuid)
        new = crud_thema.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(schema=schemas.Thema, old=old, new=new).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/themas",
    response_model=List[schemas.Thema],
    response_model_exclude=defer_attributes,
)
def read_valid_themas(
    crud_thema: CRUDThema = Depends(deps.get_crud_thema),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the themas lineages and shows the latests valid object for each.
    """
    themas = crud_thema.valid(offset=offset, limit=limit, filters=filters)
    return themas


@router.get("/valid/themas/{lineage_id}", response_model=List[schemas.Thema])
def read_valid_thema_lineage(
    lineage_id: int,
    crud_thema: CRUDThema = Depends(deps.get_crud_thema),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the themas in this lineage that are valid
    """
    themas = crud_thema.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not themas:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return themas


@router.get("/version/themas/{object_uuid}", response_model=schemas.Thema)
def read_latest_version_lineage(
    object_uuid: str,
    crud_thema: CRUDThema = Depends(deps.get_crud_thema),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    themas = crud_thema.get_latest_by_uuid(uuid=object_uuid)

    if not themas:
        raise HTTPException(status_code=404, detail="Thema lineage not found")

    return themas
