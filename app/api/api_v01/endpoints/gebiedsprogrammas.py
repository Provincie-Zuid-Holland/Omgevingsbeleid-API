from http import HTTPStatus
from typing import Any, List
from app.schemas.filters import Filters

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app import crud, models, schemas
from app.api import deps
from app.models.gebruiker import GebruikersRol
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {"Omschrijving"}


@router.get(
    "/gebiedsprogrammas",
    response_model=List[schemas.Gebiedsprogramma],
    response_model_exclude=defer_attributes,
)
def read_gebiedsprogrammas(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the gebiedsprogrammas lineages and shows the latests object for each
    """
    gebiedsprogrammas = crud.gebiedsprogramma.latest(
        all=True,
        offset=offset,
        limit=limit,
        filters=filters,
    )

    return gebiedsprogrammas


@router.post(
    "/gebiedsprogrammas",
    response_model=schemas.Gebiedsprogramma,
    status_code=HTTPStatus.CREATED,
)
def create_gebiedsprogramma(
    *,
    db: Session = Depends(deps.get_db),
    gebiedsprogramma_in: schemas.GebiedsprogrammaCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new gebiedsprogrammas lineage
    """
    gebiedsprogramma = crud.gebiedsprogramma.create(
        obj_in=gebiedsprogramma_in, by_uuid=current_gebruiker.UUID
    )
    return gebiedsprogramma


@router.get(
    "/gebiedsprogrammas/{lineage_id}", response_model=List[schemas.Gebiedsprogramma]
)
def read_gebiedsprogramma_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the gebiedsprogrammas versions by lineage
    """
    gebiedsprogrammas = crud.gebiedsprogramma.all(filters=Filters({"ID": lineage_id}))
    if not gebiedsprogrammas:
        raise HTTPException(status_code=404, detail="Gebiedsprogrammas not found")
    return gebiedsprogrammas


@router.patch(
    "/gebiedsprogrammas/{lineage_id}", response_model=schemas.Gebiedsprogramma
)
def update_gebiedsprogramma(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    gebiedsprogramma_in: schemas.GebiedsprogrammaUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new gebiedsprogrammas to a lineage
    """
    gebiedsprogramma = crud.gebiedsprogramma.get_latest_by_id(id=lineage_id)
    if not gebiedsprogramma:
        raise HTTPException(status_code=404, detail="Gebiedsprogramma not found")
    if gebiedsprogramma.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    gebiedsprogramma = crud.gebiedsprogramma.update(
        db_obj=gebiedsprogramma, obj_in=gebiedsprogramma_in
    )
    return gebiedsprogramma


@router.get("/changes/gebiedsprogrammas/{old_uuid}/{new_uuid}")
def changes_gebiedsprogrammas(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of gebiedsprogrammas.
    """
    try:
        old = crud.gebiedsprogramma.get(old_uuid)
        new = crud.gebiedsprogramma.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )
    json_data = Comparator(
        schema=schemas.Gebiedsprogramma, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/gebiedsprogrammas",
    response_model=List[schemas.Gebiedsprogramma],
    response_model_exclude=defer_attributes,
)
def read_valid_gebiedsprogrammas(
    db: Session = Depends(deps.get_db),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the gebiedsprogrammas lineages and shows the latests valid object for each.
    """
    gebiedsprogrammas = crud.gebiedsprogramma.valid(
        offset=offset,
        limit=limit,
        filters=filters,
    )
    return gebiedsprogrammas


@router.get(
    "/valid/gebiedsprogrammas/{lineage_id}",
    response_model=List[schemas.Gebiedsprogramma],
)
def read_valid_gebiedsprogramma_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the gebiedsprogrammas in this lineage that are valid
    """
    gebiedsprogrammas = crud.gebiedsprogramma.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return gebiedsprogrammas
