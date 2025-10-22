from typing import List

from app.core.tables.users import UsersTable
from app.tests.fixtures.types import FixturesType, UserFactory, FixtureContext


def fixtures(context: FixtureContext) -> FixturesType:
    password: str = context.security.get_password_hash("password")
    return [
        UserFactory(id=1, rol="Superuser", wachtwoord=password),
        UserFactory(id=2, rol="Ambtelijk opdrachtgever", wachtwoord=password),
        UserFactory(id=3, rol="Behandelend Ambtenaar", wachtwoord=password),
        UserFactory(id=4, rol="Beheerder", wachtwoord=password),
        UserFactory(id=5, rol="Portefeuillehouder", wachtwoord=password),
        UserFactory(id=6, rol="Test runner", wachtwoord=password),
        UserFactory(id=7, rol="Tester", wachtwoord=password),
    ]
