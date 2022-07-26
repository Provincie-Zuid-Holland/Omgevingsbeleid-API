from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
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
    "/beleidsprestaties",
    response_model=List[schemas.Beleidsprestatie],
    response_model_exclude=defer_attributes,
)
def read_beleidsprestaties(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsprestaties lineages and shows the latests object for each
    """
    beleidsprestaties = crud.beleidsprestatie.latest(
        all=True, filters=filters, offset=offset, limit=limit 
    )

    return beleidsprestaties


@router.post("/beleidsprestaties", response_model=schemas.Beleidsprestatie)
def create_beleidsprestatie(
    *,
    db: Session = Depends(deps.get_db),
    beleidsprestatie_in: schemas.BeleidsprestatieCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsprestaties lineage
    """
    beleidsprestatie = crud.beleidsprestatie.create(
        obj_in=beleidsprestatie_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsprestatie


@router.get("/beleidsprestaties/{lineage_id}", response_model=List[schemas.Beleidsprestatie])
def read_beleidsprestatie_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the beleidsprestaties versions by lineage
    """
    beleidsprestaties = crud.beleidsprestatie.all(ID=lineage_id)
    if not beleidsprestaties:
        raise HTTPException(status_code=404, detail="Beleidsprestaties not found")
    return beleidsprestaties


@router.patch("/beleidsprestaties/{lineage_id}", response_model=schemas.Beleidsprestatie)
def update_beleidsprestatie(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    beleidsprestatie_in: schemas.BeleidsprestatieUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidsprestaties to a lineage
    """
    beleidsprestatie = crud.beleidsprestatie.get_latest_by_id(id=lineage_id)
    if not beleidsprestatie:
        raise HTTPException(status_code=404, detail="Beleidsprestatie not found")
    if beleidsprestatie.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsprestatie = crud.beleidsprestatie.update(db_obj=beleidsprestatie, obj_in=beleidsprestatie_in)
    return beleidsprestatie


@router.get("/changes/beleidsprestaties/{old_uuid}/{new_uuid}")
def changes_beleidsprestaties(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of beleidsprestaties.
    """
    try:
        old = crud.beleidsprestatie.get(old_uuid)
        new = crud.beleidsprestatie.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    c = Comparator(schemas.Beleidsprestatie, old, new)
    json_data = jsonable_encoder({"old": old, "changes": c.compare_objects()})

    return JSONResponse(content=json_data)


@router.get(
    "/valid/beleidsprestaties",
    response_model=List[schemas.Beleidsprestatie],
    response_model_exclude=defer_attributes,
)
def read_valid_beleidsprestaties(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
) -> Any:
    """
    Gets all the beleidsprestaties lineages and shows the latests valid object for each.
    """
    beleidsprestaties = crud.beleidsprestatie.valid(
        offset=offset, limit=limit, criteria=parse_filter_str(all_filters)
    )
    return beleidsprestaties


@router.get(
    "/valid/beleidsprestaties/{lineage_id}", response_model=List[schemas.Beleidsprestatie]
)
def read_valid_beleidsprestatie_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the beleidsprestaties in this lineage that are valid
    """
    beleidsprestaties = crud.beleidsprestatie.valid(ID=lineage_id, offset=offset, limit=limit)
    return beleidsprestaties
