import logging
from typing import Any, List

from fastapi import APIRouter, Depends

from app.api.deps import get_crud_gebruiker, get_current_active_gebruiker
from app.crud.crud_gebruiker import CRUDGebruiker
from app.schemas import Gebruiker, GebruikerInline

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/gebruikers", response_model=List[GebruikerInline])
def gebruikers(
    current_gebruiker: Gebruiker = Depends(get_current_active_gebruiker),
    crud_gebruiker: CRUDGebruiker = Depends(get_crud_gebruiker),
) -> Any:
    """
    List the users of this application
    """
    gebruikers = crud_gebruiker.list()

    if not gebruikers:
        return []

    return gebruikers
