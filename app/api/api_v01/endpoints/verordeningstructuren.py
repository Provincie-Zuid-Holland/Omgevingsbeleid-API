from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDVerordeningstructuur
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()


@router.get(
    "/verordeningstructuren",
    response_model=List[schemas.Verordeningstructuur],
)
def read_verordeningstructuren(
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the verordeningstructuren lineages and shows the latests object for each
    """
    verordeningstructuren = crud_verordeningstructuur.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return verordeningstructuren


@router.post("/verordeningstructuren", response_model=schemas.Verordeningstructuur)
def create_verordeningstructuur(
    *,
    verordeningstructuur_in: schemas.VerordeningstructuurCreate,
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new verordeningstructuren lineage
    """
    verordeningstructuur = crud_verordeningstructuur.create(
        obj_in=verordeningstructuur_in, by_uuid=current_gebruiker.UUID
    )
    return verordeningstructuur


@router.get(
    "/verordeningstructuren/{lineage_id}",
    response_model=List[schemas.Verordeningstructuur],
)
def read_verordeningstructuur_lineage(
    *,
    lineage_id: int,
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the verordeningstructuren versions by lineage
    """
    verordeningstructuren = crud_verordeningstructuur.all(
        filters=Filters({"ID": lineage_id})
    )
    if not verordeningstructuren:
        raise HTTPException(status_code=404, detail="Verordeningstructuurs not found")
    return verordeningstructuren


@router.patch(
    "/verordeningstructuren/{lineage_id}", response_model=schemas.Verordeningstructuur
)
def update_verordeningstructuur(
    *,
    lineage_id: int,
    verordeningstructuur_in: schemas.VerordeningstructuurUpdate,
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new verordeningstructuren to a lineage
    """
    verordeningstructuur = crud_verordeningstructuur.get_latest_by_id(id=lineage_id)
    if not verordeningstructuur:
        raise HTTPException(status_code=404, detail="Verordeningstructuur not found")
    if verordeningstructuur.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    verordeningstructuur = crud_verordeningstructuur.update(
        db_obj=verordeningstructuur,
        obj_in=verordeningstructuur_in,
        by_uuid=str(current_gebruiker.UUID),
    )
    return verordeningstructuur


@router.get("/changes/verordeningstructuren/{old_uuid}/{new_uuid}")
def changes_verordeningstructuren(
    old_uuid: str,
    new_uuid: str,
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
) -> Any:
    """
    Shows the changes between two versions of verordeningstructuren.
    """
    try:
        old = crud_verordeningstructuur.get(old_uuid)
        new = crud_verordeningstructuur.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Verordeningstructuur, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/verordeningstructuren",
    response_model=List[schemas.Verordeningstructuur],
)
def read_valid_verordeningstructuren(
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the verordeningstructuren lineages and shows the latests valid object for each.
    """
    verordeningstructuren = crud_verordeningstructuur.valid(
        offset=offset, limit=limit, filters=filters
    )
    return verordeningstructuren


@router.get(
    "/valid/verordeningstructuren/{lineage_id}",
    response_model=List[schemas.Verordeningstructuur],
)
def read_valid_verordeningstructuur_lineage(
    lineage_id: int,
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the verordeningstructuren in this lineage that are valid
    """
    verordeningstructuren = crud_verordeningstructuur.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )

    if not verordeningstructuren:
        raise HTTPException(status_code=404, detail="Lineage not found")

    return verordeningstructuren


@router.get(
    "/version/verordeningstructuren/{object_uuid}",
    response_model=schemas.Verordeningstructuur,
    operation_id="read_verordeningstructuur_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_verordeningstructuren: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    verordeningstructuren = crud_verordeningstructuren.get_latest_by_uuid(
        uuid=object_uuid
    )

    if not verordeningstructuren:
        raise HTTPException(
            status_code=404, detail="Verordeningstructuur lineage not found"
        )

    return verordeningstructuren
