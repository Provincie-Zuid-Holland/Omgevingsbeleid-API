import logging
from typing import Any, List
from uuid import UUID
from devtools import debug

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.services import graph_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/graph",
    response_model=schemas.GraphView,
)
def graph(
    db: Session = Depends(deps.get_db),
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
) -> Any:
    """
    Fetch graph representations on relationships of generic models
    """
    try:
        graph_data = graph_service.calculate_relations()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error building relational graph")

    return graph_data
