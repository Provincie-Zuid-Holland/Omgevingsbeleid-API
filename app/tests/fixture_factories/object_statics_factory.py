from uuid import UUID
from sqlalchemy.orm import Session

from app.dynamic.db.object_static_table import ObjectStaticsTable

from .fixture_factory import FixtureDataFactory


class ObjectStaticsFixtureFactory(FixtureDataFactory):
    def __init__(self, db: Session):
        super().__init__(db)

    def populate_db(self):
        for obj_static in self.objects:
            self._db.add(obj_static)

        self._db.commit()

    def create_all_objects(self):
        for obj_static_data in self._data():
            self._create_object(obj_static_data)

    def _create_object(self, data):
        obj_static = ObjectStaticsTable(**data)
        self.objects.append(obj_static)
        return obj_static

    def _data(self):
        return [
            {
                "Object_Type": "ambitie",
                "Object_ID": 1,
                "Code": "ambitie-1",
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            {
                "Object_Type": "ambitie",
                "Object_ID": 2,
                "Code": "ambitie-2",
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000002"),
            },
            {
                "Object_Type": "beleidsdoel",
                "Object_ID": 1,
                "Code": "beleidsdoel-1",
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            {
                "Object_Type": "beleidsdoel",
                "Object_ID": 2,
                "Code": "beleidsdoel-2",
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000002"),
            },
            {
                "Object_Type": "beleidskeuze",
                "Object_ID": 1,
                "Code": "beleidskeuze-1",
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            {
                "Object_Type": "beleidskeuze",
                "Object_ID": 2,
                "Code": "beleidskeuze-2",
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000002"),
            },
            {
                "Object_Type": "maatregel",
                "Object_ID": 1,
                "Code": "maatregel-1",
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            {
                "Object_Type": "maatregel",
                "Object_ID": 2,
                "Code": "maatregel-2",
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000002"),
            },
        ]
