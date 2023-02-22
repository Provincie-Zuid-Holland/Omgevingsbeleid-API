from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from app import schemas
from app.api import deps
from app.crud import CRUDGebiedsprogramma
from app.models.gebruiker import Gebruiker, GebruikersRol
from app.schemas.filters import Filters
from app.util.compare import Comparator

router = APIRouter()

defer_attributes = {
    "Omschrijving",
    "Weblink",
}


@router.get(
    "/gebiedsprogrammas",
    response_model=List[schemas.Gebiedsprogramma],
    response_model_exclude=defer_attributes,
)
def read_gebiedsprogrammas(
    crud_gebiedsprogramma: CRUDGebiedsprogramma = Depends(
        deps.get_crud_gebiedsprogramma
    ),
    current_gebruiker: Gebruiker = Depends(deps.get_current_active_gebruiker),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the gebiedsprogrammas lineages and shows the latests object for each
    """
    gebiedsprogrammas = crud_gebiedsprogramma.latest(
        all=True,
        offset=offset,
        limit=limit,
        filters=filters,
    )

    return gebiedsprogrammas


@router.post("/gebiedsprogrammas", response_model=schemas.Gebiedsprogramma)
def create_gebiedsprogramma(
    *,
    gebiedsprogramma_in: schemas.GebiedsprogrammaCreate,
    crud_gebiedsprogramma: CRUDGebiedsprogramma = Depends(
        deps.get_crud_gebiedsprogramma
    ),
    current_gebruiker: Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Creates a new gebiedsprogrammas lineage
    """
    gebiedsprogramma = crud_gebiedsprogramma.create(
        obj_in=gebiedsprogramma_in, by_uuid=str(current_gebruiker.UUID)
    )
    return gebiedsprogramma


@router.get(
    "/gebiedsprogrammas/{lineage_id}", response_model=List[schemas.Gebiedsprogramma]
)
def read_gebiedsprogramma_lineage(
    *,
    lineage_id: int,
    crud_gebiedsprogramma: CRUDGebiedsprogramma = Depends(
        deps.get_crud_gebiedsprogramma
    ),
    current_gebruiker: Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Gets all the gebiedsprogrammas versions by lineage
    """
    gebiedsprogrammas = crud_gebiedsprogramma.all(filters=Filters({"ID": lineage_id}))
    if not gebiedsprogrammas:
        raise HTTPException(status_code=404, detail="Gebiedsprogrammas not found")
    return gebiedsprogrammas


@router.patch(
    "/gebiedsprogrammas/{lineage_id}", response_model=schemas.Gebiedsprogramma
)
def update_gebiedsprogramma(
    *,
    lineage_id: int,
    gebiedsprogramma_in: schemas.GebiedsprogrammaUpdate,
    crud_gebiedsprogramma: CRUDGebiedsprogramma = Depends(
        deps.get_crud_gebiedsprogramma
    ),
    current_gebruiker: Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Adds a new gebiedsprogrammas to a lineage
    """
    gebiedsprogramma = crud_gebiedsprogramma.get_latest_by_id(id=lineage_id)
    if not gebiedsprogramma:
        raise HTTPException(status_code=404, detail="Gebiedsprogramma not found")
    if gebiedsprogramma.Created_By.UUID != current_gebruiker.UUID:
        if current_gebruiker.Rol != GebruikersRol.SUPERUSER:
            raise HTTPException(
                status_code=403, detail="Forbidden: Not the owner of this resource"
            )
    gebiedsprogramma = crud_gebiedsprogramma.update(
        db_obj=gebiedsprogramma,
        obj_in=gebiedsprogramma_in,
        by_uuid=str(current_gebruiker.UUID),
    )
    return gebiedsprogramma


@router.get("/changes/gebiedsprogrammas/{old_uuid}/{new_uuid}")
def changes_gebiedsprogrammas(
    old_uuid: str,
    new_uuid: str,
    crud_gebiedsprogramma: CRUDGebiedsprogramma = Depends(
        deps.get_crud_gebiedsprogramma
    ),
    current_gebruiker: Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Shows the changes between two versions of gebiedsprogrammas.
    """
    try:
        old = crud_gebiedsprogramma.get(old_uuid)
        new = crud_gebiedsprogramma.get(new_uuid)
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
    crud_gebiedsprogramma: CRUDGebiedsprogramma = Depends(
        deps.get_crud_gebiedsprogramma
    ),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the gebiedsprogrammas lineages and shows the latests valid object for each.
    """
    gebiedsprogrammas = crud_gebiedsprogramma.valid(
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
    crud_gebiedsprogramma: CRUDGebiedsprogramma = Depends(
        deps.get_crud_gebiedsprogramma
    ),
    filters: Filters = Depends(deps.string_filters),
    offset: int = 0,
    limit: int = 20,
) -> Any:
    """
    Gets all the gebiedsprogrammas in this lineage that are valid
    """
    gebiedsprogrammas = crud_gebiedsprogramma.valid(
        ID=lineage_id, offset=offset, limit=limit, filters=filters
    )
    if not gebiedsprogrammas:
        raise HTTPException(
            status_code=404, detail="Gebiedsprogramma lineage not found"
        )
    return gebiedsprogrammas


@router.get(
    "/version/gebiedsprogrammas/{object_uuid}",
    response_model=schemas.Gebiedsprogramma,
    operation_id="read_gebiedsprogramma_version",
)
def read_latest_version_lineage(
    object_uuid: str,
    crud_gebiedsprogramma: CRUDGebiedsprogramma = Depends(
        deps.get_crud_gebiedsprogramma
    ),
) -> Any:
    """
    Finds the lineage of the resource and retrieves the latest
    available version.
    """
    try:
        UUID(object_uuid)
    except ValueError:
        raise HTTPException(status_code=403, detail="UUID not in valid format")

    gebiedsprogrammas = crud_gebiedsprogramma.get_latest_by_uuid(uuid=object_uuid)

    if not gebiedsprogrammas:
        raise HTTPException(
            status_code=404, detail="Gebiedsprogramma lineage not found"
        )

    return gebiedsprogrammas
