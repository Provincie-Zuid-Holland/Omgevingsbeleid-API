from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.ambitie import Ambitie 
from app.models.gebruiker import GebruikersRol

router = APIRouter()


@router.get(
    "/ambities",
    response_model=List[schemas.Ambitie],
    response_model_exclude={"Omschrijving"},
)
def read_ambities(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
) -> Any:
    """
    Gets all the ambities lineages and shows the latests object for each
    """
    ambities = crud.ambitie.latest(offset=offset, limit=limit)
    return ambities


@router.post("/ambities", response_model=schemas.Ambitie)
def create_ambitie(
    *,
    db: Session = Depends(deps.get_db),
    ambitie_in: schemas.AmbitieCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new ambities lineage
    """
    ambitie = crud.ambitie.create(obj_in=ambitie_in, by_uuid=current_gebruiker.UUID)
    return ambitie


@router.get("/ambities/{lineage_id}", response_model=List[schemas.Ambitie])
def read_ambitie(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the ambities versions by lineage
    """
    ambities = crud.ambitie.all(ID=lineage_id)
    if not ambities:
        raise HTTPException(status_code=404, detail="Ambities not found")
    return ambities


@router.patch("/ambities/{lineage_id}", response_model=schemas.Ambitie)
def update_ambitie(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    ambitie_in: schemas.AmbitieUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new ambities to a lineage
    """
    ambitie = crud.ambitie.get_latest_by_id(id=lineage_id)
    if not ambitie:
        raise HTTPException(status_code=404, detail="Ambitie not found")
    if ambitie.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    ambitie = crud.ambitie.update(db_obj=ambitie, obj_in=ambitie_in)
    return ambitie


@router.get(
    "/changes/ambities/{old_uuid}/{new_uuid}", response_model=List[schemas.Ambitie]
)
def changes_ambities(
    old_uuid: str,
    new_uuid: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Shows the changes between two versions of ambities-
    """
    ambities = crud.ambitie.get_multi(db=db, skip=offset, limit=limit)
    return ambities


@router.get("/valid/ambities", response_model=List[schemas.Ambitie], response_model_exclude={"Omschrijving"})
def read_ambities(
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
) -> Any:
    """
    Gets all the ambities lineages and shows the latests valid object for each.
    """
    ambities = crud.ambitie.valid()
    return ambities


@router.get("/valid/ambities/{lineage_id}", response_model=List[schemas.Ambitie])
def read_ambities(
    lineage_id: str,
    offset: int = 0,
    limit: int = 20,
    all_filters: str = "",
    any_filters: str = "",
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the ambities in this lineage that are valid
    """
    ambities = crud.ambitie.valid()
    return ambities
