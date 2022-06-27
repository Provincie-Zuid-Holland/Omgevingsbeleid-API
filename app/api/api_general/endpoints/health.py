
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps

router = APIRouter()


@router.get("/")
@router.head("/")
def health_request(db: Session = Depends(deps.get_db)) -> bool:
    return True
