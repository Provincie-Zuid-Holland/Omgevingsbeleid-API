from typing import List

from app.core.tables.objects import ObjectStaticsTable
from app.tests.fixtures.types import FixtureContext, ObjectStaticsFactory


def fixtures(_: FixtureContext) -> List[ObjectStaticsTable]:
    return [
        ObjectStaticsFactory(id=1, object_type="ambitie", owner_id=1).create(),
        ObjectStaticsFactory(id=2, object_type="ambitie", owner_id=1).create(),
        ObjectStaticsFactory(id=3, object_type="ambitie", owner_id=1).create(),
        ObjectStaticsFactory(id=4, object_type="ambitie", owner_id=1).create(),
        ObjectStaticsFactory(id=5, object_type="ambitie", owner_id=1).create(),
        ObjectStaticsFactory(id=1, object_type="beleidsdoel", owner_id=1).create(),
        ObjectStaticsFactory(id=2, object_type="beleidsdoel", owner_id=2).create(),
        ObjectStaticsFactory(id=1, object_type="beleidskeuze", owner_id=1).create(),
        ObjectStaticsFactory(id=2, object_type="beleidskeuze", owner_id=2).create(),
        ObjectStaticsFactory(id=1, object_type="maatregel", owner_id=1).create(),
        ObjectStaticsFactory(id=2, object_type="maatregel", owner_id=2).create(),
        ObjectStaticsFactory(id=1, object_type="werkingsgebied", owner_id=1).create(),
        ObjectStaticsFactory(id=1, object_type="document", owner_id=1).create(),
        ObjectStaticsFactory(id=2, object_type="document", owner_id=1).create(),
    ]
