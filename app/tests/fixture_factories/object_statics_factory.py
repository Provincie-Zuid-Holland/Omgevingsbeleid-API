from collections import defaultdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.dynamic.db.object_static_table import ObjectStaticsTable

from .fixture_factory import FixtureDataFactory


class ObjectStaticsFixtureFactory(FixtureDataFactory):
    def __init__(self, db: Session, local_tables=None):
        super().__init__(db)
        self.local_tables = local_tables

    def populate_db(self):
        if len(self.objects) == 0:
            self.create_all_objects()
        for obj_static in self.objects:
            self._db.add(obj_static)

        self._db.commit()

    def create_all_objects(self):
        for obj_static_data in self._data():
            self._create_object(obj_static_data)

    def _create_object(self, data):
        dynamic_attributes = {
            key: data.pop(key) for key in list(data) if key not in ObjectStaticsTable.__table__.columns.keys()
        }

        if self.local_tables:
            static_obj = self.local_tables.ObjectStaticsTable(**data)
        else:
            static_obj = ObjectStaticsTable(**data)

        # Set the dynamically added attributes on the instance
        for key, value in dynamic_attributes.items():
            setattr(static_obj, key, value)

        self.objects.append(static_obj)
        return static_obj

    def _data(self):
        base_data = [
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
                "Owner_1_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            {
                "Object_Type": "maatregel",
                "Object_ID": 2,
                "Code": "maatregel-2",
            },
        ]

        updated_base_data = [self.generate_sample_data(custom_values=item) for item in base_data]
        return updated_base_data

    def generate_sample_data(self, custom_values=None):
        # Default values
        default_values = defaultdict(None)
        default_values["Object_ID"] = 1
        default_values["Object_Type"] = "beleidskeuze"
        default_values["Owner_1_UUID"] = UUID("11111111-0000-0000-0000-000000000002")
        default_values["Owner_2_UUID"] = None
        default_values["Client_1_UUID"] = UUID("11111111-0000-0000-0000-000000000005")

        if custom_values:
            default_values.update(custom_values)

        return dict(default_values)
