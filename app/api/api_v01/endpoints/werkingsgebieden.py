from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDWerkingsgebied
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {}


@router.get(
    "/werkingsgebieden",
    response_model=List[schemas.Werkingsgebied],
    response_model_exclude=defer_attributes,
)
def read_werkingsgebied(
    crud_werkingsgebied: CRUDWerkingsgebied = Depends(deps.get_crud_werkingsgebied),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = -1,
) -> Any:
    """
    Gets all the werkingsgebied lineages and shows the latests object for each
    """
    werkingsgebied = crud_werkingsgebied.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )
    return werkingsgebied


@router.post("/werkingsgebieden", response_model=schemas.Werkingsgebied)
def create_werkingsgebied(
    *,
    werkingsgebied_in: schemas.WerkingsgebiedCreate,
    crud_werkingsgebied: CRUDWerkingsgebied = Depends(deps.get_crud_werkingsgebied),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new werkingsgebied lineage
    """
    werkingsgebied = crud_werkingsgebied.create(
        obj_in=werkingsgebied_in, by_uuid=current_gebruiker.UUID
    )
    return werkingsgebied


@router.get(
    "/werkingsgebieden/{lineage_id}", response_model=List[schemas.Werkingsgebied]
)
def read_werkingsgebied_lineage(
    *,
    lineage_id: int,
    crud_werkingsgebied: CRUDWerkingsgebied = Depends(deps.get_crud_werkingsgebied),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the werkingsgebied versions by lineage
    """
    werkingsgebied = crud_werkingsgebied.all(filters=Filters({"ID": lineage_id}))
    if not werkingsgebied:
        raise HTTPException(status_code=404, detail="werkingsgebied not found")
    return werkingsgebied


@router.patch("/werkingsgebieden/{lineage_id}", response_model=schemas.Werkingsgebied)
def update_werkingsgebied(
    *,
    lineage_id: int,
    werkingsgebied_in: schemas.WerkingsgebiedUpdate,
    crud_werkingsgebied: CRUDWerkingsgebied = Depends(deps.get_crud_werkingsgebied),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new werkingsgebied to a lineage
    """
    werkingsgebied = crud_werkingsgebied.get_latest_by_id(id=lineage_id)
    if not werkingsgebied:
        raise HTTPException(status_code=404, detail="Werkingsgebied not found")
    if werkingsgebied.Created_By.UUID != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    werkingsgebied = crud_werkingsgebied.update(
        db_obj=werkingsgebied,
        obj_in=werkingsgebied_in,
        by_uuid=str(current_gebruiker.UUID),
    )
    return werkingsgebied


@router.get("/changes/werkingsgebieden/{old_uuid}/{new_uuid}")
def changes_werkingsgebied(
    old_uuid: str,
    new_uuid: str,
    crud_werkingsgebied: CRUDWerkingsgebied = Depends(deps.get_crud_werkingsgebied),
) -> Any:
    """
    Shows the changes between two versions of werkingsgebied.
    """
    try:
        old = crud_werkingsgebied.get(old_uuid)
        new = crud_werkingsgebied.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Werkingsgebied, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/werkingsgebieden",
    response_model=List[schemas.Werkingsgebied],
    response_model_exclude=defer_attributes,
)
def read_valid_werkingsgebied(
    crud_werkingsgebied: CRUDWerkingsgebied = Depends(deps.get_crud_werkingsgebied),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = -1,
) -> Any:
    """
    Gets all the werkingsgebied lineages and shows the latests valid object for each.
    """
    werkingsgebied = crud_werkingsgebied.valid(
        offset=offset, limit=limit, filters=filters
    )
    return werkingsgebied


@router.get(
    "/valid/werkingsgebieden/{lineage_id}", response_model=List[schemas.Werkingsgebied]
)
def read_valid_werkingsgebied_lineage(
    lineage_id: int,
    crud_werkingsgebied: CRUDWerkingsgebied = Depends(deps.get_crud_werkingsgebied),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = -1,
) -> Any:
    """
    Gets all the werkingsgebied in this lineage that are valid
    """
    werkingsgebied = crud_werkingsgebied.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not werkingsgebied:
        raise HTTPException(status_code=404, detail="Beleidsregels lineage not found")
    return werkingsgebied


@router.get(
    "/version/werkingsgebieden/{object_uuid}",
    response_model=schemas.Werkingsgebied,
    operation_id="read_werkingsgebied_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_werkingsgebieden: CRUDWerkingsgebied = Depends(deps.get_crud_werkingsgebied),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    werkingsgebieden = crud_werkingsgebieden.get_latest_by_uuid(uuid=object_uuid)

    if not werkingsgebieden:
        raise HTTPException(status_code=404, detail="Werkingsgebied lineage not found")

    return werkingsgebieden
