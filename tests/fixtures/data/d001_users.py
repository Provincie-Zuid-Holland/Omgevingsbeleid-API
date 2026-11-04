from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    col.adds(
        [
            UserSpec(
                key="admin",
                name="Admin",
                email="admin@pzh.nl",
                roles=["Superuser"],
            ),
            UserSpec(
                key="ambtenaar",
                name="Ambtenaar Alice",
                email="alice@pzh.nl",
                roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="manager_of_module_4",
                name="Ambtenaar Bernard",
                email="manager_of_module_4@pzh.nl",
                roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="viewer",
                name="Viewer",
                email="viewer@pzh.nl",
                roles=["Portefeuillehouder"],
            ),
            UserSpec(
                key="owner_1",
                name="Owner of a few objects",
                email="owner_1@pzh.nl",
                roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="owner_3",
                name="Third owner of a few objects",
                email="owner_3@pzh.nl",
                roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="frozen",
                name="Frozen",
                email="frozen@pzh.nl",
                roles=["Behandelend Ambtenaar"],
            ),
            UserSpec(
                key="beheerder",
                name="beheerder",
                email="beheerder@pzh.nl",
                roles=["Technisch Beheerder"],
            ),
        ]
    )
