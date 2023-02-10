from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDBeleidsrelatie
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {"Omschrijving"}

@router.get("/beleidsrelaties", response_model=List[schemas.Beleidsrelatie])
def read_beleidsrelaties(
    crud_beleidsrelatie: CRUDBeleidsrelatie = Depends(deps.get_crud_beleidsrelatie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsrelaties lineages and shows the latests object for each
    """
    beleidsrelaties = crud_beleidsrelatie.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsrelaties


@router.post("/beleidsrelaties", response_model=schemas.Beleidsrelatie)
def create_beleidsrelatie(
    *,
    beleidsrelatie_in: schemas.BeleidsrelatieCreate,
    crud_beleidsrelatie: CRUDBeleidsrelatie = Depends(deps.get_crud_beleidsrelatie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsrelaties lineage
    """
    beleidsrelatie = crud_beleidsrelatie.create(
        obj_in=beleidsrelatie_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsrelatie


@router.get(
    "/beleidsrelaties/{lineage_id}", response_model=List[schemas.Beleidsrelatie]
)
def read_beleidsrelatie_lineage(
    *,
    lineage_id: int,
    crud_beleidsrelatie: CRUDBeleidsrelatie = Depends(deps.get_crud_beleidsrelatie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the beleidsrelaties versions by lineage
    """
    beleidsrelaties = crud_beleidsrelatie.all(filters=Filters({"ID": lineage_id}))
    if not beleidsrelaties:
        raise HTTPException(status_code=404, detail="Beleidsrelatie lineage not found")
    return beleidsrelaties


@router.patch("/beleidsrelaties/{lineage_id}", response_model=schemas.Beleidsrelatie)
def update_beleidsrelatie(
    *,
    lineage_id: int,
    beleidsrelatie_in: schemas.BeleidsrelatieUpdate,
    crud_beleidsrelatie: CRUDBeleidsrelatie = Depends(deps.get_crud_beleidsrelatie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidsrelaties to a lineage
    """
    beleidsrelatie = crud_beleidsrelatie.get_latest_by_id(id=lineage_id)
    if not beleidsrelatie:
        raise HTTPException(status_code=404, detail="Beleidsrelatie not found")
    if beleidsrelatie.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsrelatie = crud_beleidsrelatie.update(
        db_obj=beleidsrelatie,
        obj_in=beleidsrelatie_in,
        by_uuid=str(current_gebruiker.UUID),
    )
    return beleidsrelatie


@router.get("/changes/beleidsrelaties/{old_uuid}/{new_uuid}")
def changes_beleidsrelaties(
    old_uuid: str,
    new_uuid: str,
    crud_beleidsrelatie: CRUDBeleidsrelatie = Depends(deps.get_crud_beleidsrelatie),
) -> Any:
    """
    Shows the changes between two versions of beleidsrelaties.
    """
    try:
        old = crud_beleidsrelatie.get(old_uuid)
        new = crud_beleidsrelatie.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Beleidsrelatie, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/beleidsrelaties",
    response_model=List[schemas.Beleidsrelatie],
    response_model_exclude=defer_attributes,
)
def read_valid_beleidsrelaties(
    crud_beleidsrelatie: CRUDBeleidsrelatie = Depends(deps.get_crud_beleidsrelatie),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsrelaties lineages and shows the latests valid object for each.
    """
    beleidsrelaties = crud_beleidsrelatie.valid(
        offset=offset, limit=limit, filters=filters
    )
    return beleidsrelaties


@router.get(
    "/valid/beleidsrelaties/{lineage_id}", response_model=List[schemas.Beleidsrelatie]
)
def read_valid_beleidsrelatie_lineage(
    lineage_id: int,
    crud_beleidsrelatie: CRUDBeleidsrelatie = Depends(deps.get_crud_beleidsrelatie),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsrelaties in this lineage that are valid
    """
    beleidsrelaties = crud_beleidsrelatie.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not beleidsrelaties:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return beleidsrelaties


@router.get(
    "/version/beleidsrelaties/{object_uuid}",
    response_model=schemas.Beleidsrelatie,
    operation_id="read_beleidsrelatie_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_beleidsrelatie: CRUDBeleidsrelatie = Depends(deps.get_crud_beleidsrelatie),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    beleidsrelaties = crud_beleidsrelatie.get_latest_by_uuid(uuid=object_uuid)

    if not beleidsrelaties:
        raise HTTPException(status_code=404, detail="Beleidsrelatie lineage not found")

    return beleidsrelaties
