from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    col.adds(
        [
            UserSpec(
                key="admin",
                Gebruikersnaam="Admin",
                Email="admin@pzh.nl",
                Rol="Beheerder",
            ),
            UserSpec(
                key="alice",
                Gebruikersnaam="Alice",
                Email="alice@pzh.nl",
                Rol="Behandelend Ambtenaar",
            ),
            UserSpec(
                key="viewer",
                Gebruikersnaam="Viewer",
                Email="viewer@pzh.nl",
                Rol="Portefeuillehouder",
            ),
            UserSpec(
                key="frozen",
                Gebruikersnaam="Frozen",
                Email="frozen@pzh.nl",
                Rol="Behandelend Ambtenaar",
            ),
        ]
    )
