from app.dynamic.db import ObjectsTable
from unittest.mock import MagicMock, create_autospec
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class FakeExtension:
    def __init__(self):
        self.calls = []

    def initialize(self, config):
        self.calls.append(("initialize", config))

    def register_listeners(self, *args):
        self.calls.append(("register_listeners", args))

    def register_commands(self, *args):
        self.calls.append(("register_commands", args))

    def register_base_columns(self):
        self.calls.append(("register_base_columns",))
        return []

    def register_base_fields(self):
        self.calls.append(("register_base_fields",))
        return []

    def register_endpoint_resolvers(self, *args):
        self.calls.append(("register_endpoint_resolvers", args))
        return []

    def register_tables(self, *args):
        self.calls.append(("register_tables", args))

    def register_models(self, *args):
        self.calls.append(("register_models", args))

    def register_endpoints(self, *args):
        self.calls.append(("register_endpoints", args))


def get_mock_objectstable(attr_list=None):
    attributes = [
        "Object_ID",
        "Object_Type",
        "Created_Date",
        "Modified_Date",
        "Adjust_On",
        "Created_By_UUID",
        "Modified_By_UUID",
        "Start_Validity",
        "End_Validity",
        "Title",
        "Description",
        "Description_Choice",
        "Description_Operation",
        "Provincial_Interest",
        "Cause",
        "Consideration",
        "Decision_Number",
        "Explanation",
        "Explanation_Raw",
        "Weblink",
        "Tags",
        "IDMS_Link",
        "Gebied_UUID",
        "Gebied_Duiding",
    ]

    if attr_list:
        attributes = attr_list

    MockObjectsTable = create_autospec(
        ObjectsTable, **{attr: MagicMock() for attr in attributes}
    )

    return MockObjectsTable


class MockResponseModel(BaseModel):
    Object_ID: Optional[str]
    UUID: UUID
    Object_Type: str
    Modified_Date: Optional[datetime]
    Start_Validity: datetime
    End_Validity: Optional[datetime]
