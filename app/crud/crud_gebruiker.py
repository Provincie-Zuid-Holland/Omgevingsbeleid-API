from typing import Any, Dict, List, Optional, Union

from sqlalchemy.exc import NoResultFound

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.db.base_class import NULL_UUID
from app.models.gebruiker import Gebruiker
from app.schemas.gebruiker import GebruikerCreate, GebruikerUpdate


class CRUDGebruiker(CRUDBase[Gebruiker, GebruikerCreate, GebruikerUpdate]):
    def get_by_email(self, email: str) -> Optional[Gebruiker]:
        return self.db.query(Gebruiker).filter(Gebruiker.Email == email).one()

    def create(self, *, obj_in: GebruikerCreate) -> Gebruiker:
        db_obj = Gebruiker(
            Gebruikersnaam=obj_in.Gebruikersnaam,
            Wachtwoord=get_password_hash(obj_in.Wachtwoord),
            Rol=obj_in.Rol,
            Email=obj_in.Email,
            Status=obj_in.Status,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        *,
        db_obj: Gebruiker,
        obj_in: Union[GebruikerUpdate, Dict[str, Any]],
    ) -> Gebruiker:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db_obj=db_obj, obj_in=update_data)

    def authenticate(self, username: str, password: str) -> Optional[Gebruiker]:
        try:
            gebruiker = self.get_by_email(email=username)
            hashed_pw = getattr(gebruiker, "Wachtwoord")

            if not verify_password(password, hashed_pw):
                return None

            return gebruiker
        except NoResultFound:
            return None

    def list(self) -> List[Gebruiker]:
        query = self.db.query(Gebruiker).filter(Gebruiker.UUID != NULL_UUID)
        return query.all()
