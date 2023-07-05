import pytest
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.dynamic.event.types import Event, Listener
from app.dynamic.event_dispatcher import EventDispatcher


class MockEvent(Event):
    def __init__(self, message: str):
        super().__init__()
        self.message = message


class MockListener(Listener[MockEvent]):
    def handle_event(self, event: MockEvent) -> MockEvent:
        event.message = "handled"
        return event


class TestEventDispatcher:
    @pytest.fixture(scope="function")
    def event_dispatcher(self):
        return EventDispatcher()

    def test_register(self, event_dispatcher):
        listener = MockListener()
        event_dispatcher.register(listener)
        assert len(event_dispatcher._listeners) == 1

    def test_dispatch(self, event_dispatcher, db: Session):
        event_dispatcher.provide_db(db)
        event_dispatcher.provide_task_runner(BackgroundTasks())
        event_dispatcher.register(MockListener())

        event = MockEvent("testy")
        result = event_dispatcher.dispatch(event)

        assert result.message == "handled"
