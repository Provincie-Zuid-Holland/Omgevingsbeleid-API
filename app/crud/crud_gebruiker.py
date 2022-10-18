from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.gebruiker import Gebruiker
from app.schemas.gebruiker import GebruikerCreate, GebruikerUpdate


class CRUDGebruiker(CRUDBase[Gebruiker, GebruikerCreate, GebruikerUpdate]):
    def get_by_email(self, email: str) -> Optional[Gebruiker]:
        return self.db.query(Gebruiker).filter(Gebruiker.Email == email).first()

    def create(self, db: Session, *, obj_in: GebruikerCreate) -> Gebruiker:
        db_obj = Gebruiker(
            Gebruikersnaam=obj_in.Gebruikersnaam,
            Wachtwoord=get_password_hash(obj_in.Wachtwoord),
            Rol=obj_in.Rol,
            Email=obj_in.Email,
            Status=obj_in.Status,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Gebruiker,
        obj_in: Union[GebruikerUpdate, Dict[str, Any]]
    ) -> Gebruiker:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[Gebruiker]:
        gebruiker = self.get_by_email(db, email=email)
        print("\n\n\nGebruiker:")
        print(gebruiker)
        print("\n\n\n")
        if not gebruiker:
            return None
        if not verify_password(password, gebruiker.Wachtwoord):
            return None
        return gebruiker

    def is_active(self, gebruiker: Gebruiker) -> bool:
        return gebruiker.is_active


gebruiker = CRUDGebruiker(Gebruiker)
