from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.extensions.modules.db import ModuleObjectContextTable, ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.models.models import ModuleStatusCode, ModuleStatusCodeInternal

from .fixture_factory import FixtureDataFactory


class ModuleFixtureFactory(FixtureDataFactory):
    def __init__(self, db: Session, local_tables=None):
        super().__init__(db)
        self.local_tables = local_tables

        self.modules = []
        self.module_histories = []
        self.module_objects = []
        self.module_object_contexts = []

    def populate_db(self):
        for module in self.modules:
            self._db.add(module)

        for module_object_context in self.module_object_contexts:
            self._db.add(module_object_context)

        for module_object in self.module_objects:
            self._db.add(module_object)

        self._db.commit()

    def create_all_objects(self):
        self.create_all_modules()

    def _create_object(self, data):
        self._create_module(data)

    # Modules
    def create_all_modules(self):
        for module_data in self._data():
            self._create_module(module_data)

    def _create_module(self, data):
        if self.local_tables:
            module_obj = self.local_tables.ModuleTable(**data)
        else:
            module_obj = ModuleTable(**data)

        self.modules.append(module_obj)
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
            {
                "Module_ID": 2,
                "Title": "Fixture module B, locked",
                "Description": "Fixture is locked, manager is BA user",
                "Module_Manager_1_UUID": UUID("11111111-0000-0000-0000-000000000002"),
                "Created_Date": datetime(2023, 2, 2, 2, 2, 2),
                "Modified_Date": datetime(2023, 2, 2, 2, 2, 2),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000002"),
                "Modified_By_UUID": UUID("11111111-0000-0000-0000-000000000002"),
                "Activated": 1,
                "Closed": 0,
                "Successful": 0,
                "Temporary_Locked": 1,
            },
            {
                "Module_ID": 3,
                "Title": "Fixture module c",
                "Description": "Manager Beheerder user. ",
                "Module_Manager_1_UUID": UUID("11111111-0000-0000-0000-000000000004"),
                "Created_Date": datetime(2023, 2, 2, 2, 2, 2),
                "Modified_Date": datetime(2023, 2, 2, 2, 2, 2),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000004"),
                "Modified_By_UUID": UUID("11111111-0000-0000-0000-000000000004"),
                "Activated": 1,
                "Closed": 0,
                "Successful": 0,
                "Temporary_Locked": 0,
            },
            # Add more module data here as needed
        ]

    # Status History
    def create_all_module_status_history(self):
        for module in self.modules:
            for status_history_data in self._module_status_history_data(module.Module_ID):
                self._create_module_status_history(module, status_history_data)

    def _create_module_status_history(self, module, data):
        if self.local_tables:
            status_history_obj = self.local_tables.ModuleStatusHistoryTable(**data)
        else:
            status_history_obj = ModuleStatusHistoryTable(**data)

        module.status_history.append(status_history_obj)

    def _module_status_history_data(self, module_id):
        return [
            {
                "Module_ID": module_id,
                "Status": ModuleStatusCodeInternal.Niet_Actief,
                "Created_Date": datetime(2023, 2, 2, 2, 2, 2),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            {
                "Module_ID": module_id,
                "Status": ModuleStatusCode.Vastgesteld,
                "Created_Date": datetime(2023, 2, 3, 3, 3, 3),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            # Add more module status history data here as needed
        ]

    # Module objects
    def create_all_module_objects(self):
        for module in self.modules:
            for module_object_data in self._module_objects_data(module.Module_ID):
                self._create_module_object(module, module_object_data)

    def _create_module_object(self, module, data):
        if self.local_tables:
            module_object_obj = self.local_tables.ModuleObjectsTable(**data)
        else:
            module_object_obj = ModuleObjectsTable(**data)

        self.module_objects.append(module_object_obj)
        return module_object_obj

    def _module_objects_data(self, module_id):
        return [
            {
                "Module_ID": module_id,
                "Object_Type": "ambitie",
                "Object_ID": 1,
                "Code": "ambitie-1",
                "UUID": uuid4(),
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
                "UUID": uuid4(),
                "Title": "Titel van de tweede ambitie",
                "Created_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Modified_Date": datetime(2023, 2, 2, 3, 3, 3),
                "Created_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
                "Modified_By_UUID": UUID("11111111-0000-0000-0000-000000000001"),
            },
            # Add more module objects data here as needed
        ]

    # Context objects
    def create_all_module_object_context(self):
        for module in self.modules:
            for module_object_context_data in self._module_object_context_data(module.Module_ID):
                self._create_module_object_context(module_object_context_data)

    def _create_module_object_context(self, data):
        if self.local_tables:
            module_object_context_obj = self.local_tables.ModuleObjectContextTable(**data)
        else:
            module_object_context_obj = ModuleObjectContextTable(**data)

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
