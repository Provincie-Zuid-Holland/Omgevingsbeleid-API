from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.crud import (
    CRUDAmbitie,
    CRUDBelang,
    CRUDBeleidskeuze,
    CRUDBeleidsmodule,
    CRUDBeleidsdoel,
    CRUDBeleidsprestatie,
    CRUDBeleidsrelatie,
    CRUDBeleidsregel,
    CRUDMaatregel,
    CRUDThema,
    CRUDVerordening,
    CRUDVerordeningstructuur,
    CRUDGebruiker,
    CRUDWerkingsgebied,
)
from app.db.session import SessionLocal
from app.models import (
    Ambitie,
    Belang,
    Beleidskeuze,
    Beleidsmodule,
    Beleidsdoel,
    Beleidsprestatie,
    Beleidsrelatie,
    Beleidsregel,
    Maatregel,
    Thema,
    Verordening,
    Verordeningstructuur,
    Gebruiker,
    Werkingsgebied,
)
from app.schemas import TokenPayload
from app.schemas.filters import FilterCombiner, Filters
from app.services import SearchService, GeoSearchService
from app.services.graph import GraphService


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V01_STR}/login/access-token"
)


def string_filters(
    all_filters: Optional[str] = None,
    any_filters: Optional[str] = None,
) -> Filters:
    filters = Filters()
    if all_filters:
        filters.add_from_string(FilterCombiner.AND, all_filters)

    if any_filters:
        filters.add_from_string(FilterCombiner.OR, any_filters)

    return filters


def get_db() -> SessionLocal:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_crud_ambitie(db: Session = Depends(get_db)) -> CRUDAmbitie:
    return CRUDAmbitie(
        model=Ambitie,
        db=db,
    )


def get_crud_belang(db: Session = Depends(get_db)) -> CRUDBelang:
    return CRUDBelang(
        model=Belang,
        db=db,
    )


def get_crud_beleidsdoel(db: Session = Depends(get_db)) -> CRUDBeleidsdoel:
    return CRUDBeleidsdoel(
        model=Beleidsdoel,
        db=db,
    )


def get_crud_beleidskeuze(db: Session = Depends(get_db)) -> CRUDBeleidskeuze:
    return CRUDBeleidskeuze(
        model=Beleidskeuze,
        db=db,
    )


def get_crud_beleidsmodule(db: Session = Depends(get_db)) -> CRUDBeleidsmodule:
    return CRUDBeleidsmodule(
        model=Beleidsmodule,
        db=db,
    )


def get_crud_beleidsprestatie(db: Session = Depends(get_db)) -> CRUDBeleidsprestatie:
    return CRUDBeleidsprestatie(
        model=Beleidsprestatie,
        db=db,
    )


def get_crud_beleidsregel(db: Session = Depends(get_db)) -> CRUDBeleidsregel:
    return CRUDBeleidsregel(
        model=Beleidsregel,
        db=db,
    )


def get_crud_beleidsrelatie(db: Session = Depends(get_db)) -> CRUDBeleidsrelatie:
    return CRUDBeleidsrelatie(
        model=Beleidsrelatie,
        db=db,
        crud_beleidskeuze=Depends(get_crud_beleidskeuze),
    )


def get_crud_maatregel(db: Session = Depends(get_db)) -> CRUDMaatregel:
    return CRUDMaatregel(
        model=Maatregel,
        db=db,
    )


def get_crud_thema(db: Session = Depends(get_db)) -> CRUDThema:
    return CRUDThema(
        model=Thema,
        db=db,
    )


def get_crud_verordening(db: Session = Depends(get_db)) -> CRUDVerordening:
    return CRUDVerordening(
        model=Verordening,
        db=db,
    )


def get_crud_verordeningstructuur(
    db: Session = Depends(get_db),
) -> CRUDVerordeningstructuur:
    return CRUDVerordeningstructuur(
        model=Verordeningstructuur,
        db=db,
    )


def get_crud_gebruiker(db: Session = Depends(get_db)) -> CRUDGebruiker:
    return CRUDGebruiker(
        model=Gebruiker,
        db=db,
    )


def get_crud_werkingsgebied(
    db: Session = Depends(get_db),
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(get_crud_beleidskeuze),
    crud_maatregel: CRUDMaatregel = Depends(get_crud_maatregel),
) -> CRUDWerkingsgebied:
    return CRUDWerkingsgebied(
        model=Werkingsgebied,
        db=db,
        crud_beleidskeuze=crud_beleidskeuze,
        crud_maatregel=crud_maatregel,
    )


def get_search_service(
    db: Session = Depends(get_db),
    crud_ambitie: CRUDAmbitie = Depends(get_crud_ambitie),
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(get_crud_beleidskeuze),
    crud_belang: CRUDBelang = Depends(get_crud_belang),
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(get_crud_beleidsdoel),
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(get_crud_beleidsprestatie),
    crud_beleidsregel: CRUDBeleidsregel = Depends(get_crud_beleidsregel),
    crud_maatregel: CRUDMaatregel = Depends(get_crud_maatregel),
    crud_thema: CRUDThema = Depends(get_crud_thema),
):
    return SearchService(
        db=db,
        search_entities=[
            crud_ambitie,
            crud_beleidskeuze,
            crud_belang,
            crud_beleidsdoel,
            crud_beleidsprestatie,
            crud_beleidsregel,
            crud_maatregel,
            crud_thema,
        ],
    )


def get_geo_search_service(
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(get_crud_beleidskeuze),
    crud_maatregel: CRUDMaatregel = Depends(get_crud_maatregel),
    crud_verordening: CRUDVerordening = Depends(get_crud_verordening),
):
    return GeoSearchService(
        geo_cruds=[
            crud_beleidskeuze,
            crud_maatregel,
            crud_verordening,
        ]
    )


def get_graph_service(
    db: Session = Depends(get_db),
    crud_ambitie: CRUDAmbitie = Depends(get_crud_ambitie),
    crud_beleidskeuze: CRUDBeleidskeuze = Depends(get_crud_beleidskeuze),
    crud_belang: CRUDBelang = Depends(get_crud_belang),
    crud_beleidsdoel: CRUDBeleidsdoel = Depends(get_crud_beleidsdoel),
    crud_beleidsprestatie: CRUDBeleidsprestatie = Depends(get_crud_beleidsprestatie),
    crud_beleidsregel: CRUDBeleidsregel = Depends(get_crud_beleidsregel),
    crud_maatregel: CRUDMaatregel = Depends(get_crud_maatregel),
    crud_thema: CRUDThema = Depends(get_crud_thema),
    crud_verordening: CRUDVerordening = Depends(get_crud_verordening),
):
    return GraphService(
        db=db,
        graphable_model_services=[
            crud_ambitie,
            crud_beleidskeuze,
            crud_belang,
            crud_beleidsdoel,
            crud_beleidsprestatie,
            crud_beleidsregel,
            crud_maatregel,
            crud_thema,
            crud_verordening,
        ],
    )


def get_current_gebruiker(
    crud_gebruiker: CRUDGebruiker = Depends(get_crud_gebruiker),
    token: str = Depends(reusable_oauth2),
) -> Gebruiker:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kan inloggegevens niet valideren",
        )

    try:
        return crud_gebruiker.get(uuid=token_data.sub)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")


def get_current_active_gebruiker(
    current_gebruiker: Gebruiker = Depends(get_current_gebruiker),
) -> Gebruiker:
    if not current_gebruiker.is_active():
        raise HTTPException(status_code=400, detail="Gebruiker is inactief")
    return current_gebruiker
