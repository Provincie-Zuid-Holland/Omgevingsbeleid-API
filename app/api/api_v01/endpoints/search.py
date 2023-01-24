import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps
from app.core.exceptions import EmptySearchCriteria
from app.schemas.search import SearchResultWrapper
from app.services import GeoSearchService, SearchService
from app.util import get_filtered_search_criteria, get_limited_list

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search", response_model=SearchResultWrapper)
def search(
    query: str,
    only: Optional[str] = None,
    exclude: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
    search_service: SearchService = Depends(deps.get_search_service),
) -> Any:
    """
    Fetches items matching the search query parameters
    """
    # Validate filters
    if only and exclude:
        raise HTTPException(
            status_code=403, detail="cannot use both exclude and only parameters"
        )

    # Filter searchables
    searchables_to_exclude = list()

    if only is not None:
        only_list = [item.strip().lower() for item in only.split(",")]
        for crud in search_service.search_entities:
            if crud.model.__name__.lower() not in only_list:
                searchables_to_exclude.append(crud)

    if exclude is not None:
        exclude_list = [item.strip().lower() for item in exclude.split(",")]
        for crud in search_service.search_entities:
            if crud.model.__name__.lower() in exclude_list:
                searchables_to_exclude.append(crud)

    # exclude from search
    for crud in searchables_to_exclude:
        search_service.search_entities.remove(crud)

    # Sanitize stopwords or other word filters
    try:
        search_criteria = get_filtered_search_criteria(query)
    except EmptySearchCriteria:
        raise HTTPException(
            status_code=403, detail="Search query empty after filtering"
        )

    # Execute search
    search_results = search_service.search_all(search_criteria=search_criteria)

    # Map back to response format
    results = list()
    total = 0
    for item in search_results:
        search_fields = item.object.get_search_fields()
        search_description = search_fields.description

        try:
            description = getattr(item.object, search_description[0].key)
            search_result = schemas.SearchResult(
                Titel=item.object.Titel,
                Omschrijving=description,
                Type=item.object.__tablename__,
                RANK=item.rank,
                UUID=item.object.UUID,
            )
            results.append(search_result)
            total += 1
        except AttributeError:
            logger.error(
                f"Description value not found for {type(item.object)}: {item.object.UUID}"
            )

    results = get_limited_list(results, limit=limit, offset=offset)

    return SearchResultWrapper(results=results, total=total)


@router.get("/geo-search", response_model=SearchResultWrapper)
def geo_search(
    query: str,
    only: Optional[str] = None,
    exclude: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
    search_service: GeoSearchService = Depends(deps.get_geo_search_service),
) -> Any:
    """
    Lookup geo-searchable entities related to a 'Werkingsgebied'
    """
    # Validate filters
    if only and exclude:
        raise HTTPException(
            status_code=403, detail="cannot use both exclude and only parameters"
        )

    # Filter searchables
    searchables_to_exclude = list()

    if only is not None:
        only_list = [item.strip().lower() for item in only.split(",")]
        for crud in search_service.search_entities:
            if crud.model.__name__.lower() not in only_list:
                searchables_to_exclude.append(crud)

    if exclude is not None:
        exclude_list = [item.strip().lower() for item in exclude.split(",")]
        for crud in search_service.search_entities:
            if crud.model.__name__.lower() in exclude_list:
                searchables_to_exclude.append(crud)

    # exclude from search
    for crud in searchables_to_exclude:
        search_service.search_entities.remove(crud)

    try:
        query_list = [uuid for uuid in query.split(",")]
    except Exception:
        raise HTTPException(
            status_code=403, detail="Invalid list of Werkingsgebied UUIDs"
        )

    search_results = search_service.geo_search(query_list)
    results = get_limited_list(search_results, limit=limit, offset=offset)

    return SearchResultWrapper(results=results, total=len(search_results))
