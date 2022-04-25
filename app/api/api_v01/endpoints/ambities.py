from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Ambitie])
def read_ambities(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Retrieve ambities.
    """
    ambities = crud.ambitie.get_multi_by_owner(
        db=db, owner_id=current_gebruiker.id, skip=skip, limit=limit
    )
    return ambities


@router.post("/", response_model=schemas.Ambitie)
def create_ambitie(
    *,
    db: Session = Depends(deps.get_db),
    ambitie_in: schemas.AmbitieCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Create new ambitie.
    """
    ambitie = crud.ambitie.create(db=db, obj_in=ambitie_in, owner_id=current_gebruiker.id)
    return ambitie


@router.put("/{id}", response_model=schemas.Ambitie)
def update_ambitie(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    ambitie_in: schemas.AmbitieUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Update an ambitie.
    """
    ambitie = crud.ambitie.get(db=db, id=id)
    if not ambitie:
        raise HTTPException(status_code=404, detail="Ambitie not found")
    if ambitie.Created_By != current_gebruiker.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    ambitie = crud.ambitie.update(db=db, db_obj=ambitie, obj_in=ambitie_in)
    return ambitie


@router.get("/{id}", response_model=schemas.Ambitie)
def read_ambitie(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Get ambitie by ID.
    """
    ambitie = crud.ambitie.get(db=db, id=id)
    if not ambitie:
        raise HTTPException(status_code=404, detail="Ambitie not found")
    if ambitie.Created_By != current_gebruiker.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return ambitie


@router.delete("/{id}", response_model=schemas.Ambitie)
def delete_ambitie(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Delete an ambitie.
    """
    ambitie = crud.ambitie.get(db=db, id=id)
    if not ambitie:
        raise HTTPException(status_code=404, detail="Ambitie not found")
    if ambitie.Created_By != current_gebruiker.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    ambitie = crud.ambitie.remove(db=db, id=id)
    return ambitie
