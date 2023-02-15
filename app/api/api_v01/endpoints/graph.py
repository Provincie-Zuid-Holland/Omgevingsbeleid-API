import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api.deps import get_current_active_gebruiker, get_graph_service
from app.models.gebruiker import Gebruiker
from app.services.graph import GraphService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/graph", response_model=schemas.GraphView)
def graph(
    graph_service: GraphService = Depends(get_graph_service),
) -> Any:
    """
    Fetch graph representations on relationships of generic models
    """
    try:
        return graph_service.calculate_relations()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error building relational graph")
