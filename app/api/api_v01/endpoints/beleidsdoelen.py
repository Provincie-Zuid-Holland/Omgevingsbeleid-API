from http import HTTPStatus
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
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
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidsdoelen lineages and shows the latests object for each
    """
    beleidsdoelen = crud.beleidsdoel.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidsdoelen


@router.post(
    "/beleidsdoelen", response_model=schemas.Beleidsdoel, status_code=HTTPStatus.CREATED
)
def create_beleidsdoel(
    *,
    db: Session = Depends(deps.get_db),
    beleidsdoel_in: schemas.BeleidsdoelCreate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidsdoelen lineage
    """
    print("\n\n\n")
    print("start of create_beleidsdoel")
    from pprint import pprint
    pprint(beleidsdoel_in.__dict__)
    print("\n\n")
    beleidsdoel = crud.beleidsdoel.create(
        obj_in=beleidsdoel_in,
        by_uuid=current_gebruiker.UUID,
    )
    print("\nBeforereturn=")
    print(beleidsdoel)
    return beleidsdoel


@router.get("/beleidsdoelen/{lineage_id}", response_model=List[schemas.Beleidsdoel])
def read_beleidsdoel_lineage(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the beleidsdoelen versions by lineage
    """
    beleidsdoelen = crud.beleidsdoel.all(filters=Filters({"ID": lineage_id}))
    if not beleidsdoelen:
        raise HTTPException(status_code=404, detail="Beleidsdoels not found")
    return beleidsdoelen


@router.patch("/beleidsdoelen/{lineage_id}", response_model=schemas.Beleidsdoel)
def update_beleidsdoel(
    *,
    db: Session = Depends(deps.get_db),
    lineage_id: int,
    beleidsdoel_in: schemas.BeleidsdoelUpdate,
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new beleidsdoelen to a lineage
    """
    beleidsdoel = crud.beleidsdoel.get_latest_by_id(id=lineage_id)
    if not beleidsdoel:
        raise HTTPException(status_code=404, detail="Beleidsdoel not found")
    if beleidsdoel.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidsdoel = crud.beleidsdoel.update(db_obj=beleidsdoel, obj_in=beleidsdoel_in)
    return beleidsdoel


@router.get("/changes/beleidsdoelen/{old_uuid}/{new_uuid}")
def changes_beleidsdoelen(
    old_uuid: str,
    new_uuid: str,
) -> Any:
    """
    Shows the changes between two versions of beleidsdoelen.
    """
    try:
        old = crud.beleidsdoel.get(old_uuid)
        new = crud.beleidsdoel.get(new_uuid)
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
    db: Session = Depends(deps.get_db),
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
) -> Any:
    """
    Gets all the beleidsdoelen lineages and shows the latests valid object for each.
    """
    beleidsdoelen = crud.beleidsdoel.valid(offset=offset, limit=limit, filters=filters)
    return beleidsdoelen


@router.get(
    "/valid/beleidsdoelen/{lineage_id}", response_model=List[schemas.Beleidsdoel]
)
def read_valid_beleidsdoel_lineage(
    lineage_id: int,
    offset: int = 0,
    limit: int = 20,
    filters: Filters = Depends(deps.string_filters),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Gets all the beleidsdoelen in this lineage that are valid
    """
    beleidsdoelen = crud.beleidsdoel.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    return beleidsdoelen
