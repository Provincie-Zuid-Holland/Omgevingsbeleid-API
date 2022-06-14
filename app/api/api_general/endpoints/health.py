from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app import crud, models, schemas
from app.api import deps
from app.models.ambitie import Ambitie
from app.models.gebruiker import GebruikersRol
from app.util.legacy_helpers import parse_filter_str
from app.util.compare import Comparator

router = APIRouter()


@router.get("/")
@router.head("/")
def health_request(db: Session = Depends(deps.get_db)) -> bool:
    return True
