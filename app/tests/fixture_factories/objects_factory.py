from uuid import UUID
from sqlalchemy.orm import Session

from app.dynamic.db.objects_table import ObjectsTable

from .fixture_factory import FixtureDataFactory


class ObjectFixtureFactory(FixtureDataFactory):
    def __init__(self, db: Session, local_tables=None):
        super().__init__(db)
        self.local_tables = local_tables

    def populate_db(self):
        if len(self.objects) == 0:
            self.create_all_objects()
        for obj in self.objects:
            self._db.add(obj)

        self._db.commit()

    def create_all_objects(self):
        for obj_data in self._data():
            self._create_object(obj_data)

    def _create_object(self, data):
        dynamic_attributes = {
            key: data.pop(key)
            for key in list(data)
            if key not in ObjectsTable.__table__.columns.keys()
        }

        if self.local_tables:
            obj = self.local_tables.ObjectsTable(**data)
        else:
            obj = ObjectsTable(**data)

        # Set the dynamically added attributes on the instance
        for key, value in dynamic_attributes.items():
            setattr(obj, key, value)

        self.objects.append(obj)
        return obj

    def _data(self):
        return [
            {
                "Object_Type": "ambitie",
                "Object_ID": 1,
                "Code": "ambitie-1",
            },
            {
                "Object_Type": "ambitie",
                "Object_ID": 2,
                "Code": "ambitie-2",
            },
            {
                "Object_Type": "beleidsdoel",
                "Object_ID": 1,
                "Code": "beleidsdoel-1",
            },
            {
                "Object_Type": "beleidsdoel",
                "Object_ID": 2,
                "Code": "beleidsdoel-2",
            },
            {
                "Object_Type": "beleidskeuze",
                "Object_ID": 1,
                "Code": "beleidskeuze-1",
            },
            {
                "Object_Type": "beleidskeuze",
                "Object_ID": 2,
                "Code": "beleidskeuze-2",
            },
            {
                "Object_Type": "beleidskeuze",
                "Object_ID": 3,
                "Code": "beleidskeuze-3",
            },
            {
                "Object_Type": "maatregel",
                "Object_ID": 1,
                "Code": "maatregel-1",
            },
            {
                "Object_Type": "maatregel",
                "Object_ID": 2,
                "Code": "maatregel-2",
            },
        ]
