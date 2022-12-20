import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps
from app.core.exceptions import EmptySearchCriteria
from app.schemas.search import SearchResultWrapper
from app.services import GeoSearchService, SearchService
from app.util import get_filtered_search_criteria

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search", response_model=SearchResultWrapper)
def search(
    query: str,
    search_service: SearchService = Depends(deps.get_search_service),
) -> Any:
    """
    Fetches items matching the search query parameters
    """
    # Sanitize stopwords or other word filters
    try:
        search_criteria = get_filtered_search_criteria(query)
    except EmptySearchCriteria:
        raise HTTPException(
            status_code=403, detail="Search query empty after filtering"
        )

    search_results = search_service.search_all(search_criteria=search_criteria)

    results = list()
    total = 0
    for item in search_results:
        search_fields = item.object.get_search_fields()
        search_description = search_fields.description

        try:
            description = getattr(item.object, search_description[0].key)
            search_result = schemas.SearchResult(
                Omschrijving=description,
                Type=item.object.__tablename__,
                RANK=item.rank,
                UUID=item.object.UUID,
            )
            results.append(search_result)
            total += 1
        except AttributeError:
            logger.debug(
                f"Description value not found for {type(item.object)}: {item.object.UUID}"
            )

    return SearchResultWrapper(results=results, total=total)


@router.get(
    "/geo-search",
    response_model=SearchResultWrapper,
)
def geo_search(
    query: str,
    geo_search_service: GeoSearchService = Depends(deps.get_geo_search_service),
) -> Any:
    """
    Lookup geo-searchable entities related to a 'Werkingsgebied'
    """
    try:
        query_list = [uuid for uuid in query.split(",")]
    except Exception:
        raise HTTPException(
            status_code=403, detail="Invalid list of Werkingsgebied UUIDs"
        )

    search_results = geo_search_service.geo_search(query_list)

    return SearchResultWrapper(results=search_results, total=len(search_results))
