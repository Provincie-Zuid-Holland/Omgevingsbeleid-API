from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDVerordening
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {"Inhoud"}


@router.get(
    "/verordeningen",
    response_model=List[schemas.Verordening],
    response_model_exclude=defer_attributes,
)
def read_verordening(
    crud_verordening: CRUDVerordening = Depends(deps.get_crud_verordening),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the verordening lineages and shows the latests object for each
    """
    verordening = crud_verordening.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return verordening


@router.post("/verordeningen", response_model=schemas.Verordening)
def create_verordening(
    *,
    verordening_in: schemas.VerordeningCreate,
    crud_verordening: CRUDVerordening = Depends(deps.get_crud_verordening),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new verordening lineage
    """
    verordening = crud_verordening.create(
        obj_in=verordening_in, by_uuid=current_gebruiker.UUID
    )
    return verordening


@router.get("/verordeningen/{lineage_id}", response_model=List[schemas.Verordening])
def read_verordening_lineage(
    *,
    lineage_id: int,
    crud_verordening: CRUDVerordening = Depends(deps.get_crud_verordening),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the verordening versions by lineage
    """
    verordening = crud_verordening.all(filters=Filters({"ID": lineage_id}))
    if not verordening:
        raise HTTPException(status_code=404, detail="verordening not found")
    return verordening


@router.patch("/verordeningen/{lineage_id}", response_model=schemas.Verordening)
def update_verordening(
    *,
    lineage_id: int,
    verordening_in: schemas.VerordeningUpdate,
    crud_verordening: CRUDVerordening = Depends(deps.get_crud_verordening),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new verordening to a lineage
    """
    verordening = crud_verordening.get_latest_by_id(id=lineage_id)
    if not verordening:
        raise HTTPException(status_code=404, detail="Verordening not found")
    if verordening.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    verordening = crud_verordening.update(
        db_obj=verordening, obj_in=verordening_in, by_uuid=str(current_gebruiker.UUID)
    )
    return verordening


@router.get("/changes/verordeningen/{old_uuid}/{new_uuid}")
def changes_verordening(
    old_uuid: str,
    new_uuid: str,
    crud_verordening: CRUDVerordening = Depends(deps.get_crud_verordening),
) -> Any:
    """
    Shows the changes between two versions of verordening.
    """
    try:
        old = crud_verordening.get(old_uuid)
        new = crud_verordening.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Verordening, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/verordeningen",
    response_model=List[schemas.Verordening],
    response_model_exclude=defer_attributes,
)
def read_valid_verordening(
    crud_verordening: CRUDVerordening = Depends(deps.get_crud_verordening),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the verordening lineages and shows the latests valid object for each.
    """
    verordening = crud_verordening.valid(offset=offset, limit=limit, filters=filters)
    return verordening


@router.get(
    "/valid/verordeningen/{lineage_id}", response_model=List[schemas.Verordening]
)
def read_valid_verordening_lineage(
    lineage_id: int,
    crud_verordening: CRUDVerordening = Depends(deps.get_crud_verordening),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the verordeningen in this lineage that are valid
    """
    verordeningen = crud_verordening.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not verordeningen:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return verordeningen


@router.get(
    "/version/verordeningen/{object_uuid}",
    response_model=schemas.Verordening,
    operation_id="read_verordening_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_verorderning: CRUDVerordening = Depends(deps.get_crud_verordening),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    verordeningen = crud_verorderning.get_latest_by_uuid(uuid=object_uuid)

    if not verordeningen:
        raise HTTPException(status_code=404, detail="Verorderning lineage not found")

    return verordeningen
