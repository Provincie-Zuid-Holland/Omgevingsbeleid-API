from uuid import UUID
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.extensions.users.db import UsersTable


class FixtureDataFactory:
    def __init__(self, db: Session):
        self._db = db
        self.users = []

    def populate_all(self):
        self.populate_users()

    def populate_users(self):
        for user_data in self._user_data():
            self._create_user(user_data)

    def _create_user(self, user_data):
        user = UsersTable(
            UUID=UUID(user_data["UUID"]),
            Gebruikersnaam=user_data["Gebruikersnaam"],
            Email=user_data["Email"],
            Rol=user_data["Rol"],
            Status=user_data["Status"],
            Wachtwoord=get_password_hash(user_data["Wachtwoord"]),
        )
        self._db.add(user)
        self.users.append(user)

    def _user_data(self):
        return [
            {
                "UUID": "11111111-0000-0000-0000-000000000001",
                "Gebruikersnaam": "Anton",
                "Email": "test@example.com",
                "Rol": "Superuser",
                "Status": "Actief",
                "Wachtwoord": "password",
            },
            {
                "UUID": "11111111-0000-0000-0000-000000000002",
                "Gebruikersnaam": "Bert",
                "Email": "b@example.com",
                "Rol": "Ambtelijk opdrachtgever",
                "Status": "Actief",
                "Wachtwoord": "password",
            },
            {
                "UUID": "11111111-0000-0000-0000-000000000003",
                "Gebruikersnaam": "Cees",
                "Email": "c@example.com",
                "Rol": "Behandelend Ambtenaar",
                "Status": "Actief",
                "Wachtwoord": "password",
            },
            {
                "UUID": "11111111-0000-0000-0000-000000000004",
                "Gebruikersnaam": "Daniel",
                "Email": "d@example.com",
                "Rol": "Beheerder",
                "Status": "Actief",
                "Wachtwoord": "password",
            },
            {
                "UUID": "11111111-0000-0000-0000-000000000005",
                "Gebruikersnaam": "Emma",
                "Email": "e@example.com",
                "Rol": "Portefeuillehouder",
                "Status": "Actief",
                "Wachtwoord": "password",
            },
            {
                "UUID": "11111111-0000-0000-0000-000000000006",
                "Gebruikersnaam": "Fred",
                "Email": "f@example.com",
                "Rol": "Test runner",
                "Status": "Actief",
                "Wachtwoord": "password",
            },
            {
                "UUID": "11111111-0000-0000-0000-000000000007",
                "Gebruikersnaam": "Gerald",
                "Email": "g@example.com",
                "Rol": "Tester",
                "Status": "Actief",
                "Wachtwoord": "password",
            },
        ]
