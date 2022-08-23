from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.gebruiker import GebruikersRol
from app.schemas.filters import Filters
from app.services import search_service
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
    search_results = search_service.search(model=models.Ambitie, query="Overstromingen parent seller")

    results = schemas.SearchResult(
        Omschrijving="Test", Type="typetesdt", RANK=69, UUID="uu00-11dd"
    )

    return [results]
