from http import HTTPStatus
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app import crud, models, schemas
from app.api import deps
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {"Omschrijving"}


@router.get(
    "/beleidsrelaties",
    response_model=List[schemas.Beleidsrelatie],
    response_model_exclude=defer_attributes,
)
def read_beleidsrelaties(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsrelaties lineages and shows the latests object for each
    """
    beleidsrelaties = crud.beleidsrelatie.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsrelaties


@router.post(
    "/beleidsrelaties",
    response_model=schemas.Beleidsrelatie,
    status_code=HTTPStatus.CREATED,
)
def create_beleidsrelatie(
    *,
    db: Session = Depends(deps.get_db),
    beleidsrelatie_in: schemas.BeleidsrelatieCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsrelaties lineage
    """
    beleidsrelatie = crud.beleidsrelatie.create(
        obj_in=beleidsrelatie_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsrelatie


@router.get(
    "/beleidsrelaties/{lineage_id}", response_model=List[schemas.Beleidsrelatie]
)
def read_beleidsrelatie_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the beleidsrelaties versions by lineage
    """
    beleidsrelaties = crud.beleidsrelatie.all(filters=Filters({"ID": lineage_id}))
    if not beleidsrelaties:
        raise HTTPException(status_code=404, detail="Beleidsrelaties not found")
    return beleidsrelaties


@router.patch("/beleidsrelaties/{lineage_id}", response_model=schemas.Beleidsrelatie)
def update_beleidsrelatie(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    beleidsrelatie_in: schemas.BeleidsrelatieUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidsrelaties to a lineage
    """
    beleidsrelatie = crud.beleidsrelatie.get_latest_by_id(id=lineage_id)
    if not beleidsrelatie:
        raise HTTPException(status_code=404, detail="Beleidsrelatie not found")
    if beleidsrelatie.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsrelatie = crud.beleidsrelatie.update(
        db_obj=beleidsrelatie, obj_in=beleidsrelatie_in
    )
    return beleidsrelatie


@router.get("/changes/beleidsrelaties/{old_uuid}/{new_uuid}")
def changes_beleidsrelaties(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of beleidsrelaties.
    """
    try:
        old = crud.beleidsrelatie.get(old_uuid)
        new = crud.beleidsrelatie.get(new_uuid)
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
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
) -> Any:
    """
    Gets all the beleidsrelaties lineages and shows the latests valid object for each.
    """
    beleidsrelaties = crud.beleidsrelatie.valid(
        offset=offset, limit=limit, filters=filters
    )
    return beleidsrelaties


@router.get(
    "/valid/beleidsrelaties/{lineage_id}", response_model=List[schemas.Beleidsrelatie]
)
def read_valid_beleidsrelatie_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the beleidsrelaties in this lineage that are valid
    """
    beleidsrelaties = crud.beleidsrelatie.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return beleidsrelaties
