from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDBeleidsdoel
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {"Omschrijving"}


@router.get(
    "/beleidsdoelen",
    response_model=List[schemas.Beleidsdoel],
    response_model_exclude=defer_attributes,
)
def read_beleidsdoelen(
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(deps.get_crud_beleidsdoel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsdoelen lineages and shows the latests object for each
    """
    beleidsdoelen = crud_beleidsdoel.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsdoelen


@router.post("/beleidsdoelen", response_model=schemas.Beleidsdoel)
def create_beleidsdoel(
    *,
    beleidsdoel_in: schemas.BeleidsdoelCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(deps.get_crud_beleidsdoel),
) -> Any:
    """
    Creates a new beleidsdoelen lineage
    """
    beleidsdoel = crud_beleidsdoel.create(
        obj_in=beleidsdoel_in, by_uuid=current_gebruiker.UUID
    )
    return beleidsdoel


@router.get("/beleidsdoelen/{lineage_id}", response_model=List[schemas.Beleidsdoel])
def read_beleidsdoel_lineage(
    *,
    lineage_id: int,
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(deps.get_crud_beleidsdoel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the beleidsdoelen versions by lineage
    """
    beleidsdoelen = crud_beleidsdoel.all(filters=Filters({"ID": lineage_id}))
    if not beleidsdoelen:
        raise HTTPException(status_code=404, detail="Beleidsdoels not found")
    return beleidsdoelen


@router.patch("/beleidsdoelen/{lineage_id}", response_model=schemas.Beleidsdoel)
def update_beleidsdoel(
    *,
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(deps.get_crud_beleidsdoel),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    lineage_id: int,
    beleidsdoel_in: schemas.BeleidsdoelUpdate,
) -> Any:
    """
    Adds a new beleidsdoelen to a lineage
    """
    beleidsdoel = crud_beleidsdoel.get_latest_by_id(id=lineage_id)
    if not beleidsdoel:
        raise HTTPException(status_code=404, detail="Beleidsdoel not found")
    if beleidsdoel.Created_By.UUID != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsdoel = crud_beleidsdoel.update(
        db_obj=beleidsdoel, obj_in=beleidsdoel_in, by_uuid=str(current_gebruiker.UUID)
    )
    return beleidsdoel


@router.get("/changes/beleidsdoelen/{old_uuid}/{new_uuid}")
def changes_beleidsdoelen(
    old_uuid: str,
    new_uuid: str,
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(deps.get_crud_beleidsdoel),
) -> Any:
    """
    Shows the changes between two versions of beleidsdoelen.
    """
    try:
        old = crud_beleidsdoel.get(old_uuid)
        new = crud_beleidsdoel.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )

    json_data = Comparator(
        schema=schemas.Beleidsdoel, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/beleidsdoelen",
    response_model=List[schemas.Beleidsdoel],
    response_model_exclude=defer_attributes,
)
def read_valid_beleidsdoelen(
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(deps.get_crud_beleidsdoel),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsdoelen lineages and shows the latests valid object for each.
    """
    beleidsdoelen = crud_beleidsdoel.valid(offset=offset, limit=limit, filters=filters)
    return beleidsdoelen


@router.get(
    "/valid/beleidsdoelen/{lineage_id}", response_model=List[schemas.Beleidsdoel]
)
def read_valid_beleidsdoel_lineage(
    lineage_id: int,
    filters: Filters = Depends(deps.string_filters),
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(deps.get_crud_beleidsdoel),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsdoelen in this lineage that are valid
    """
    beleidsdoelen = crud_beleidsdoel.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return beleidsdoelen


@router.get(
    "/version/beleidsdoelen/{object_uuid}",
    response_model=schemas.Beleidsdoel,
    operation_id="read_beleidsdoel_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(deps.get_crud_beleidsdoel),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    beleidsdoelen = crud_beleidsdoel.get_latest_by_uuid(uuid=object_uuid)

    if not beleidsdoelen:
        raise HTTPException(status_code=404, detail="Beleidsdoel lineage not found")

    return beleidsdoelen
