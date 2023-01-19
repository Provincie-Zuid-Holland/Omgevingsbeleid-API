from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDAmbitie
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import FilterCombiner, Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {
    "Omschrijving",
    "Weblink",
    "Beleidskeuzes",
}


@router.get(
    "/ambities",
    response_model=List[schemas.Ambitie],
    response_model_exclude=defer_attributes,
)
def read_ambities(
    crud_ambitie: CRUDAmbitie = Depends(deps.get_crud_ambitie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the ambities lineages and shows the latests object for each
    """
    ambities = crud_ambitie.latest(
        all=True,
        offset=offset,
        limit=limit,
        filters=filters,
    )

    return ambities


@router.post("/ambities", response_model=schemas.Ambitie)
def create_ambitie(
    *,
    ambitie_in: schemas.AmbitieCreate,
    crud_ambitie: CRUDAmbitie = Depends(deps.get_crud_ambitie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new ambities lineage
    """
    ambitie = crud_ambitie.create(
        obj_in=ambitie_in, by_uuid=str(current_gebruiker.UUID)
    )
    return ambitie


@router.get("/ambities/{lineage_id}", response_model=List[schemas.Ambitie])
def read_ambitie_lineage(
    *,
    lineage_id: int,
    crud_ambitie: CRUDAmbitie = Depends(deps.get_crud_ambitie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the ambities versions by lineage
    """
    filters.add_from_dict(FilterCombiner.AND, {"ID": lineage_id})
    ambities = crud_ambitie.all(
        filters=filters,
        offset=offset,
        limit=limit,
    )
    if not ambities:
        raise HTTPException(status_code=404, detail="Ambities not found")
    return ambities


@router.patch("/ambities/{lineage_id}", response_model=schemas.Ambitie)
def update_ambitie(
    *,
    lineage_id: int,
    ambitie_in: schemas.AmbitieUpdate,
    crud_ambitie: CRUDAmbitie = Depends(deps.get_crud_ambitie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new ambities to a lineage
    """
    ambitie = crud_ambitie.get_latest_by_id(id=lineage_id)
    if not ambitie:
        raise HTTPException(status_code=404, detail="Ambitie not found")
    if ambitie.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    ambitie = crud_ambitie.update(
        db_obj=ambitie, obj_in=ambitie_in, by_uuid=str(current_gebruiker.UUID)
    )
    return ambitie


@router.get("/changes/ambities/{old_uuid}/{new_uuid}")
def changes_ambities(
    old_uuid: str,
    new_uuid: str,
    crud_ambitie: CRUDAmbitie = Depends(deps.get_crud_ambitie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Shows the changes between two versions of ambities.
    """
    try:
        old = crud_ambitie.get(old_uuid)
        new = crud_ambitie.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )
    json_data = Comparator(schema=schemas.Ambitie, old=old, new=new).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/ambities",
    response_model=List[schemas.Ambitie],
    response_model_exclude=defer_attributes,
)
def read_valid_ambities(
    crud_ambitie: CRUDAmbitie = Depends(deps.get_crud_ambitie),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the ambities lineages and shows the latests valid object for each.
    """
    ambities = crud_ambitie.valid(
        offset=offset,
        limit=limit,
        filters=filters,
    )
    return ambities


@router.get("/valid/ambities/{lineage_id}", response_model=List[schemas.Ambitie])
def read_valid_ambitie_lineage(
    lineage_id: int,
    crud_ambitie: CRUDAmbitie = Depends(deps.get_crud_ambitie),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the ambities in this lineage that are valid
    """
    ambities = crud_ambitie.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not ambities:
        raise HTTPException(status_code=404, detail="Ambitie lineage not found")
    return ambities


@router.get(
    path="/version/ambities/{object_uuid}",
    response_model=schemas.Ambitie,
    operation_id="read_ambitie_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_ambitie: CRUDAmbitie = Depends(deps.get_crud_ambitie),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    ambities = crud_ambitie.get_latest_by_uuid(uuid=object_uuid)

    if not ambities:
        raise HTTPException(status_code=404, detail="Ambitie lineage not found")

    return ambities
