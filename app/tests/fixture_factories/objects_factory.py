from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.dynamic.db import ObjectsTable

from .fixture_factory import FixtureDataFactory


class ObjectFixtureFactory(FixtureDataFactory):
    def __init__(self, db=None, local_tables=None):
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
            key: data.pop(key) for key in list(data) if key not in ObjectsTable.__table__.columns.keys()
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
        base_data = [
            {
                "Object_Type": "ambitie",
                "Object_ID": 1,
                "Code": "ambitie-1",
            },
            {
                "Object_Type": "ambitie",
                "Object_ID": 2,
                "Code": "ambitie-1",
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

        updated_base_data = [self.generate_sample_data(custom_values=item) for item in base_data]
        return updated_base_data

    def generate_sample_data(self, custom_values=None):
        five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
        five_days_later = datetime.now(timezone.utc) + timedelta(days=5)
        # Default values
        default_values = defaultdict(None)
        default_values["Object_ID"] = 1
        default_values["Object_Type"] = "beleidskeuze"
        default_values["Start_Validity"] = five_days_ago
        default_values["End_Validity"] = five_days_later
        default_values["Created_By_UUID"] = UUID("11111111-0000-0000-0000-000000000002")
        default_values["Modified_By_UUID"] = UUID("11111111-0000-0000-0000-000000000002")
        default_values["Title"] = "Monty"
        default_values["Description"] = "Python"

        if custom_values:
            default_values.update(custom_values)

        return dict(default_values)
