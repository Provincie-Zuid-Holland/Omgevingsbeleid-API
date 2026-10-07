from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    col.adds(
        [
            UserSpec(
                key="admin",
                Gebruikersnaam="Admin",
                Email="admin@pzh.nl",
                Roles=["Superuser"],
            ),
            UserSpec(
                key="ambtenaar",
                Gebruikersnaam="Ambtenaar Alice",
                Email="alice@pzh.nl",
                Roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="manager_of_module_4",
                Gebruikersnaam="Ambtenaar Bernard",
                Email="manager_of_module_4@pzh.nl",
                Roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="viewer",
                Gebruikersnaam="Viewer",
                Email="viewer@pzh.nl",
                Roles=["Portefeuillehouder"],
            ),
            UserSpec(
                key="owner_1",
                Gebruikersnaam="Owner of a few objects",
                Email="owner_1@pzh.nl",
                Roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="owner_3",
                Gebruikersnaam="Third owner of a few objects",
                Email="owner_3@pzh.nl",
                Roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="frozen",
                Gebruikersnaam="Frozen",
                Email="frozen@pzh.nl",
                Roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="beheerder",
                Gebruikersnaam="beheerder",
                Email="beheerder@pzh.nl",
                Roles=["Technisch Beheerder"],
            ),
        ]
    )
