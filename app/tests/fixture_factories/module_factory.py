from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.extensions.modules.db import (
    ModuleTable,
    ModuleStatusHistoryTable,
    ModuleObjectContextTable,
)
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.models.models import AllModuleStatusCode
from .fixture_factory import FixtureDataFactory


class ModuleFixtureFactory(FixtureDataFactory):
    def __init__(self, db: Session):
        super().__init__(db)
        self.modules = []
        self.module_histories = []
        self.module_objects = []
        self.module_object_contexts = []

    def populate_db(self):
        for module in self.objects:
            self._db.add(module)
            # self._db.commit()

        for module_object_context in self.module_object_contexts:
            self._db.add(module_object_context)
            # self._db.commit()

        for module_object in self.module_objects:
            self._db.add(module_object)
            # self._db.commit()

        self._db.commit()

    def create_all_objects(self):
        for module_data in self._data():
            self._create_object(module_data)

    def _create_object(self, data):
        module_obj = ModuleTable(**data)
        self.objects.append(module_obj)
        return module_obj

    def _data(self):
        return [
            {
                "Module_ID": 1,
                "Title": "Fixture module A",
                "Description": "Description of fixture module A",
                "Module_Manager_1_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Created_Date": datetime(2023, 2, 2, 2, 2, 2),
                "Modified_Date": datetime(2023, 2, 2, 2, 2, 2),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Modified_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Activated": 1,
                "Closed": 0,
                "Successful": 0,
                "Temporary_Locked": 0,
            },
            # Add more module data here as needed
        ]

    def create_all_module_status_history(self):
        for module in self.objects:
            for status_history_data in self._module_status_history_data(
                module.Module_ID
            ):
                self._create_module_status_history(module, status_history_data)

    def _create_module_status_history(self, module, data):
        status_history_obj = ModuleStatusHistoryTable(**data)
        module.status_history.append(status_history_obj)

    def _module_status_history_data(self, module_id):
        return [
            {
                "Module_ID": module_id,
                "Status": AllModuleStatusCode.Niet_Actief,
                "Created_Date": datetime(2023, 2, 2, 2, 2, 2),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            {
                "Module_ID": module_id,
                "Status": AllModuleStatusCode.Vastgesteld,
                "Created_Date": datetime(2023, 2, 3, 3, 3, 3),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            # Add more module status history data here as needed
        ]

    def create_all_module_objects(self):
        for module in self.objects:
            for module_object_data in self._module_objects_data(module.Module_ID):
                self._create_module_object(module, module_object_data)

    def _create_module_object(self, module, data):
        dynamic_attributes = {
            key: data.pop(key)
            for key in list(data)
            if key not in ModuleObjectsTable.__table__.columns.keys()
        }
        module_object_obj = ModuleObjectsTable(**data)

        # Set the dynamically added attributes on the instance
        for key, value in dynamic_attributes.items():
            setattr(module_object_obj, key, value)

        self.module_objects.append(module_object_obj)
        return module_object_obj

    def _module_objects_data(self, module_id):
        return [
            {
                "Module_ID": module_id,
                "Object_Type": "ambitie",
                "Object_ID": 1,
                "Code": "ambitie-1",
                "UUID": UUID("00000000-0000-0001-0000-000000000001"),
                "Title": "Titel van de eerste ambitie",
                "Created_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Modified_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Modified_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            {
                "Module_ID": module_id,
                "Object_Type": "ambitie",
                "Object_ID": 2,
                "Code": "ambitie-2",
                "UUID": UUID("00000000-0000-0001-0000-000000000002"),
                "Title": "Titel van de tweede ambitie",
                "Created_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Modified_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Modified_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            # Add more module objects data here as needed
        ]

    def create_all_module_object_context(self):
        for module in self.objects:
            for module_object_context_data in self._module_object_context_data(
                module.Module_ID
            ):
                self._create_module_object_context(module_object_context_data)

    def _create_module_object_context(self, data):
        # module_object_context_obj = ModuleObjectContextTable(**data)

        dynamic_attributes = {
            key: data.pop(key)
            for key in list(data)
            if key not in ModuleObjectContextTable.__table__.columns.keys()
        }
        module_object_context_obj = ModuleObjectContextTable(**data)

        # Set the dynamically added attributes on the instance
        for key, value in dynamic_attributes.items():
            setattr(module_object_context_obj, key, value)

        self.module_object_contexts.append(module_object_context_obj)

        return module_object_context_obj

    def _module_object_context_data(self, module_id):
        return [
            {
                "Module_ID": module_id,
                "Object_Type": "ambitie",
                "Object_ID": 1,
                "Code": "ambitie-1",
                "Created_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Modified_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Modified_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Original_Adjust_On": None,
                "Action": "Toevoegen",
                "Explanation": "Deze wil ik toevoegen",
                "Conclusion": "Geen conclusie",
            },
            {
                "Module_ID": module_id,
                "Object_Type": "ambitie",
                "Object_ID": 2,
                "Code": "ambitie-2",
                "Created_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Modified_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Modified_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Original_Adjust_On": None,
                "Action": "Toevoegen",
                "Explanation": "Deze wil ik toevoegen",
                "Conclusion": "Geen conclusie",
            },
            # Add more module object context data here as needed
        ]
