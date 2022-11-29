from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDMaatregel
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.schemas.maatregel import MaatregelListable
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {
    "Omschrijving",
    "Gebied_Duiding",
    "Toelichting",
    "Toelichting_Raw",
    "Weblink",
    "Tags",
}


@router.get(
    "/maatregelen",
    response_model=List[MaatregelListable],
    response_model_exclude=defer_attributes,
)
def read_maatregelen(
    crud_maatregel: CRUDMaatregel = Depends(deps.get_crud_maatregel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the maatregelen lineages and shows the latests object for each
    """
    maatregelen = crud_maatregel.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return maatregelen


@router.post("/maatregelen", response_model=schemas.Maatregel)
def create_maatregel(
    *,
    maatregel_in: schemas.MaatregelCreate,
    crud_maatregel: CRUDMaatregel = Depends(deps.get_crud_maatregel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new maatregelen lineage
    """
    maatregel = crud_maatregel.create(
        obj_in=maatregel_in, by_uuid=current_gebruiker.UUID
    )
    return maatregel


@router.get("/maatregelen/{lineage_id}", response_model=List[schemas.Maatregel])
def read_maatregel_lineage(
    *,
    lineage_id: int,
    crud_maatregel: CRUDMaatregel = Depends(deps.get_crud_maatregel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the maatregel versions by lineage
    """
    maatregelen = crud_maatregel.all(filters=Filters({"ID": lineage_id}))
    if not maatregelen:
        raise HTTPException(status_code=404, detail="Maatregelen not found")
    return maatregelen


@router.patch("/maatregelen/{lineage_id}", response_model=schemas.Maatregel)
def update_maatregel(
    *,
    lineage_id: int,
    maatregel_in: schemas.MaatregelUpdate,
    crud_maatregel: CRUDMaatregel = Depends(deps.get_crud_maatregel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new maatregelen to a lineage
    """
    maatregel = crud_maatregel.get_latest_by_id(id=lineage_id)
    if not maatregel:
        raise HTTPException(status_code=404, detail="Maatregel not found")
    if maatregel.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    maatregel = crud_maatregel.update(
        db_obj=maatregel, obj_in=maatregel_in, by_uuid=str(current_gebruiker.UUID)
    )
    return maatregel


@router.get("/changes/maatregelen/{old_uuid}/{new_uuid}")
def changes_maatregelen(
    old_uuid: str,
    new_uuid: str,
    crud_maatregel: CRUDMaatregel = Depends(deps.get_crud_maatregel),
) -> Any:
    """
    Shows the changes between two versions of maatregelen.
    """
    try:
        old = crud_maatregel.get(old_uuid)
        new = crud_maatregel.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(schema=schemas.Maatregel, old=old, new=new).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/maatregelen",
    response_model=List[MaatregelListable],
    response_model_exclude=defer_attributes,
)
def read_valid_maatregelen(
    crud_maatregel: CRUDMaatregel = Depends(deps.get_crud_maatregel),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the maatregelen lineages and shows the latests valid object for each.
    """
    maatregelen = crud_maatregel.valid(offset=offset, limit=limit, filters=filters)
    return maatregelen


@router.get("/valid/maatregelen/{lineage_id}", response_model=List[schemas.Maatregel])
def read_valid_maatregel_lineage(
    lineage_id: int,
    crud_maatregel: CRUDMaatregel = Depends(deps.get_crud_maatregel),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the maatregelen in this lineage that are valid
    """
    maatregelen = crud_maatregel.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not maatregelen:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return maatregelen
