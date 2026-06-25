from typing import List

from app.core.tables.users import UsersTable
from app.tests.fixtures.types import UserFactory, FixtureContext


def fixtures(context: FixtureContext) -> List[UsersTable]:
    wachtwoord = context.security.get_password_hash("password")
    return [
        UserFactory(id=1, rol="Superuser", wachtwoord=wachtwoord).create(),
        UserFactory(id=2, rol="Ambtelijk opdrachtgever", wachtwoord=wachtwoord).create(),
        UserFactory(id=3, rol="Behandelend Ambtenaar", wachtwoord=wachtwoord).create(),
        UserFactory(id=4, rol="Beheerder", wachtwoord=wachtwoord).create(),
        UserFactory(id=5, rol="Portefeuillehouder", wachtwoord=wachtwoord).create(),
        UserFactory(id=6, rol="Test runner", wachtwoord=wachtwoord).create(),
        UserFactory(id=7, rol="Tester", wachtwoord=wachtwoord).create(),
    ]
