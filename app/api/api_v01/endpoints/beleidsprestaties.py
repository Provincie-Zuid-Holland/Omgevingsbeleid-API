from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app import crud, models, schemas
from app.api import deps
from app.crud import CRUDBeleidsprestatie
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {
    "Omschrijving",
    "Weblink",
}


@router.get(
    "/beleidsprestaties",
    response_model=List[schemas.Beleidsprestatie],
    response_model_exclude=defer_attributes,
)
def read_beleidsprestaties(
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(deps.get_crud_beleidsprestatie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsprestaties lineages and shows the latests object for each
    """
    beleidsprestaties = crud_beleidsprestatie.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsprestaties


@router.post("/beleidsprestaties", response_model=schemas.Beleidsprestatie)
def create_beleidsprestatie(
    *,
    beleidsprestatie_in: schemas.BeleidsprestatieCreate,
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(deps.get_crud_beleidsprestatie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsprestaties lineage
    """
    beleidsprestatie = crud_beleidsprestatie.create(
        obj_in=beleidsprestatie_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsprestatie


@router.get(
    "/beleidsprestaties/{lineage_id}", response_model=List[schemas.Beleidsprestatie]
)
def read_beleidsprestatie_lineage(
    *,
    lineage_id: int,
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(deps.get_crud_beleidsprestatie),
) -> Any:
    """
    Gets all the beleidsprestaties versions by lineage
    """
    beleidsprestaties = crud_beleidsprestatie.all(filters=Filters({"ID": lineage_id}))
    if not beleidsprestaties:
        raise HTTPException(status_code=404, detail="Beleidsprestaties not found")
    return beleidsprestaties


@router.patch(
    "/beleidsprestaties/{lineage_id}", response_model=schemas.Beleidsprestatie
)
def update_beleidsprestatie(
    *,
    lineage_id: int,
    beleidsprestatie_in: schemas.BeleidsprestatieUpdate,
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(deps.get_crud_beleidsprestatie),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidsprestaties to a lineage
    """
    beleidsprestatie = crud_beleidsprestatie.get_latest_by_id(id=lineage_id)
    if not beleidsprestatie:
        raise HTTPException(status_code=404, detail="Beleidsprestatie not found")
    if beleidsprestatie.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsprestatie = crud_beleidsprestatie.update(
        db_obj=beleidsprestatie, obj_in=beleidsprestatie_in
    )
    return beleidsprestatie


@router.get("/changes/beleidsprestaties/{old_uuid}/{new_uuid}")
def changes_beleidsprestaties(
    old_uuid: str,
    new_uuid: str,
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(deps.get_crud_beleidsprestatie),
) -> Any:
    """
    Shows the changes between two versions of beleidsprestaties.
    """
    try:
        old = crud_beleidsprestatie.get(old_uuid)
        new = crud_beleidsprestatie.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Beleidsprestatie, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/beleidsprestaties",
    response_model=List[schemas.Beleidsprestatie],
    response_model_exclude=defer_attributes,
)
def read_valid_beleidsprestaties(
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(deps.get_crud_beleidsprestatie),
    filters: Filters = Depends(deps.string_filters),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsprestaties lineages and shows the latests valid object for each.
    """
    beleidsprestaties = crud_beleidsprestatie.valid(
        offset=offset, limit=limit, filters=filters
    )
    return beleidsprestaties


@router.get(
    "/valid/beleidsprestaties/{lineage_id}",
    response_model=List[schemas.Beleidsprestatie],
)
def read_valid_beleidsprestatie_lineage(
    lineage_id: int,
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(deps.get_crud_beleidsprestatie),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsprestaties in this lineage that are valid
    """
    beleidsprestaties = crud_beleidsprestatie.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return beleidsprestaties
