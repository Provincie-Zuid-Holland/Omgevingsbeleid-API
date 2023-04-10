from contextlib import contextmanager, ExitStack
from pydantic import BaseModel

from app.dynamic.dynamic_app import DynamicApp


class LocalTables(BaseModel):
    Base: type
    ObjectsTable: type
    ObjectStaticsTable: type
    UsersTabel: type

    class Config:
        arbitrary_types_allowed = True


class TestDynamicApp(BaseModel):
    dynamic_app: DynamicApp
    local_tables: LocalTables

    class Config:
        arbitrary_types_allowed = True


@contextmanager
def patch_multiple(*patches):
    """
    Helper method wrap multiple patches using contextmanager.
    prevents unreadable nesting mess.
    """
    with ExitStack() as stack:
        for patch in patches:
            stack.enter_context(patch)
        yield
