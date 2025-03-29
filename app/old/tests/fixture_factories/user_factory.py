from uuid import UUID

from sqlalchemy.orm import Session

from app.core_old.security import Security
from app.core_old.settings.dynamic_settings import create_dynamic_settings
from app.extensions.users.db import UsersTable
from app.extensions.users.db.tables import IS_ACTIVE

from .fixture_factory import FixtureDataFactory


class UserFixtureFactory(FixtureDataFactory):
    def __init__(self, db: Session):
        super().__init__(db)
        self._security: Security = Security(create_dynamic_settings())

    def populate_db(self):
        if len(self.objects) == 0:
            self.create_all_objects()
        for user in self.objects:
            self._db.add(user)

        self._db.commit()

    def create_all_objects(self):
        for user_data in self._data():
            self._create_object(user_data)

    def _create_object(self, data):
        user_obj = UsersTable(**data)
        self.objects.append(user_obj)
        return user_obj

    def _data(self):
        return [
            {
                "UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Gebruikersnaam": "Anton",
                "Email": "test@example.com",
                "Rol": "Superuser",
                "Status": IS_ACTIVE,
                "Wachtwoord": self._security.get_password_hash("password"),
            },
            {
                "UUID": UUID("11111111-0000-0000-0000-000000000002"),
                "Gebruikersnaam": "Bert",
                "Email": "b@example.com",
                "Rol": "Ambtelijk opdrachtgever",
                "Status": IS_ACTIVE,
                "Wachtwoord": self._security.get_password_hash("password"),
            },
            {
                "UUID": UUID("11111111-0000-0000-0000-000000000003"),
                "Gebruikersnaam": "Cees",
                "Email": "c@example.com",
                "Rol": "Behandelend Ambtenaar",
                "Status": IS_ACTIVE,
                "Wachtwoord": self._security.get_password_hash("password"),
            },
            {
                "UUID": UUID("11111111-0000-0000-0000-000000000004"),
                "Gebruikersnaam": "Daniel",
                "Email": "d@example.com",
                "Rol": "Beheerder",
                "Status": IS_ACTIVE,
                "Wachtwoord": self._security.get_password_hash("password"),
            },
            {
                "UUID": UUID("11111111-0000-0000-0000-000000000005"),
                "Gebruikersnaam": "Emma",
                "Email": "e@example.com",
                "Rol": "Portefeuillehouder",
                "Status": IS_ACTIVE,
                "Wachtwoord": self._security.get_password_hash("password"),
            },
            {
                "UUID": UUID("11111111-0000-0000-0000-000000000006"),
                "Gebruikersnaam": "Fred",
                "Email": "f@example.com",
                "Rol": "Test runner",
                "Status": IS_ACTIVE,
                "Wachtwoord": self._security.get_password_hash("password"),
            },
            {
                "UUID": UUID("11111111-0000-0000-0000-000000000007"),
                "Gebruikersnaam": "Gerald",
                "Email": "g@example.com",
                "Rol": "Tester",
                "Status": IS_ACTIVE,
                "Wachtwoord": self._security.get_password_hash("password"),
            },
        ]
