from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import models, schemas
from app.api import deps
from app.crud import CRUDBeleidskeuze
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import FilterCombiner, Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attrs_list_view = {
    "Omschrijving",
    "Omschrijving_Keuze",
    "Omschrijving_Werking",
}


@router.get(
    "/beleidskeuzes",
    response_model=List[schemas.BeleidskeuzeListable],
)
def read_beleidskeuzes(
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(deps.get_crud_beleidskeuze),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidskeuzes lineages and shows the latests object for each
    """
    beleidskeuzes = crud_beleidskeuze.latest(
        all=True, filters=filters, offset=offset, limit=limit
    )

    return beleidskeuzes


@router.post("/beleidskeuzes", response_model=schemas.Beleidskeuze)
def create_beleidskeuze(
    *,
    beleidskeuze_in: schemas.BeleidskeuzeCreate,
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(deps.get_crud_beleidskeuze),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new beleidskeuzes lineage
    """
    beleidskeuze = crud_beleidskeuze.create(
        obj_in=beleidskeuze_in, by_uuid=current_gebruiker.UUID
    )
    return beleidskeuze


@router.get("/beleidskeuzes/{lineage_id}", response_model=List[schemas.Beleidskeuze])
def read_beleidskeuze_lineage(
    *,
    lineage_id: int,
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(deps.get_crud_beleidskeuze),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidskeuzes versions by lineage
    """
    filters.add_from_dict(FilterCombiner.AND, {"ID": lineage_id})
    beleidskeuzes = crud_beleidskeuze.all(
        filters=filters,
        offset=offset,
        limit=limit,
    )
    if not beleidskeuzes:
        raise HTTPException(status_code=404, detail="Beleidskeuzes not found")
    return beleidskeuzes


@router.patch("/beleidskeuzes/{lineage_id}", response_model=schemas.Beleidskeuze)
def update_beleidskeuze(
    *,
    lineage_id: int,
    beleidskeuze_in: schemas.BeleidskeuzeUpdate,
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(deps.get_crud_beleidskeuze),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Update latest beleidskeuze from a lineage
    """
    beleidskeuze = crud_beleidskeuze.get_latest_by_id(id=lineage_id)
    if not beleidskeuze:
        raise HTTPException(status_code=404, detail="Beleidskeuze not found")

    if beleidskeuze.Created_By != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    beleidskeuze = crud_beleidskeuze.update(
        current_bk=beleidskeuze,
        obj_in=beleidskeuze_in,
        by_uuid=str(current_gebruiker.UUID),
    )
    return beleidskeuze


@router.get("/changes/beleidskeuzes/{old_uuid}/{new_uuid}")
def changes_beleidskeuzes(
    old_uuid: str,
    new_uuid: str,
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(deps.get_crud_beleidskeuze),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Shows the changes between two versions of beleidskeuzes.
    """
    try:
        old = crud_beleidskeuze.get(old_uuid)
        new = crud_beleidskeuze.get(new_uuid)
    except NoResultFound as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object with UUID {old_uuid} or {new_uuid} does not exist.",
        )
    json_data = Comparator(
        schema=schemas.Beleidskeuze, old=old, new=new
    ).get_json_result()
    return JSONResponse(content=json_data)


@router.get(
    "/valid/beleidskeuzes",
    response_model=List[schemas.BeleidskeuzeListable],
)
def read_valid_beleidskeuzes(
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(deps.get_crud_beleidskeuze),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidskeuzes lineages and shows the latests valid object for each.
    """
    beleidskeuzes = crud_beleidskeuze.valid(offset=offset, limit=limit, filters=filters)
    return beleidskeuzes


@router.get(
    "/valid/beleidskeuzes/{lineage_id}", response_model=List[schemas.Beleidskeuze]
)
def read_valid_beleidskeuze_lineage(
    lineage_id: int,
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(deps.get_crud_beleidskeuze),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the beleidskeuzes in this lineage that are valid
    """
    beleidskeuzes = crud_beleidskeuze.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not beleidskeuzes:
        raise HTTPException(status_code=404, detail="Beleidskeuze lineage not found")

    return beleidskeuzes


@router.get(
    "/version/beleidskeuzes/{object_uuid}",
    response_model=schemas.Beleidskeuze,
    operation_id="read_beleidskeuze_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(deps.get_crud_beleidskeuze),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    beleidskeuzes = crud_beleidskeuze.get_latest_by_uuid(uuid=object_uuid)

    if not beleidskeuzes:
        raise HTTPException(status_code=404, detail="Beleidskeuze lineage not found")

    return beleidskeuzes
