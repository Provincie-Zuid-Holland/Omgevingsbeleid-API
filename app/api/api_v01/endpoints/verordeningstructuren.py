from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import models, schemas
from app.api import deps
from app.crud import CRUDVerordeningstructuur
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters

router = APIRouter()


@router.get(
    "/verordeningstructuur",
    response_model=List[schemas.Verordeningstructuur],
)
def read_verordeningstructuren(
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = -1,
) -> Any:
    """
    Gets all the actual verordeningstructuren
    """
    verordeningstructuren = crud_verordeningstructuur.actual_view(
        filters=filters, offset=offset, limit=limit
    )

    return verordeningstructuren


@router.post("/verordeningstructuur", response_model=schemas.Verordeningstructuur)
def create_verordeningstructuur(
    *,
    verordeningstructuur_in: schemas.VerordeningstructuurCreate,
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new verordeningstructuur lineage
    """
    verordeningstructuur = crud_verordeningstructuur.create(
        obj_in=verordeningstructuur_in, by_uuid=str(current_gebruiker.UUID)
    )
    return verordeningstructuur


@router.get(
    "/verordeningstructuur/{lineage_id}",
    response_model=List[schemas.Verordeningstructuur],
)
def read_verordeningstructuur_lineage(
    *,
    lineage_id: int,
    crud_verordeningstructuur: CRUDVerordeningstructuur = Depends(
        deps.get_crud_verordeningstructuur
    ),
) -> Any:
    """
    Gets all the verordeningstructuren versions by lineage
    """
    verordeningstructuren = crud_verordeningstructuur.actual_view(ID=lineage_id)

    if not verordeningstructuren:
        raise HTTPException(status_code=404, detail="Verordeningstructuur not found")

    return verordeningstructuren


@router.patch(
    "/verordeningstructuur/{lineage_id}", response_model=schemas.Verordeningstructuur
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
    Adds a new verordeningstructuur to a lineage
    """
    verordeningstructuur = crud_verordeningstructuur.get_latest_by_id(id=lineage_id)
    if not verordeningstructuur:
        raise HTTPException(status_code=404, detail="Verordeningstructuur not found")
    if verordeningstructuur.Created_By.UUID != current_gebruiker.UUID:
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


@router.get(
    "/version/verordeningstructuur/{object_uuid}",
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
