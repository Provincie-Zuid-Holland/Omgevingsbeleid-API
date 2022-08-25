from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.exceptions import SearchException
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.services import search_service
from app.util import word_filter
from app.util.compare import Comparator

router = APIRouter()


@router.get(
    "/search",
    response_model=List[schemas.SearchResult],
)
def search(
    query: str,
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Fetches items matching the search query parameters
    """
    search_results = search_service.search_all(
        search_query=query
    )
    results = list()
    for item in search_results:
        model = item.object
        search_fields = model.get_search_fields().description
        try:
            description = getattr(model, search_fields[0].key)
            results.append(
                schemas.SearchResult(
                    Omschrijving=description,
                    Type=model.__tablename__,
                    RANK=item.rank, 
                    UUID=model.UUID
                )
            )
        except AttributeError:
            raise SearchException(f"Description value not found for {type(model)}: {model.UUID}")

    return results

