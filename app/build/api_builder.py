from dependency_injector.wiring import inject, Provide

from app.core.settings import Settings
from .build_container import BuilderContainer

from sqlalchemy.orm import Session



class ApiBuilder:
    @inject
    def __init__(
        self,
        settings: Settings = Provide[BuilderContainer.settings],
        db: Session = Provide[BuilderContainer.db],
        main_config: dict = Provide[BuilderContainer.main_config],
    ):
        self._settings: Settings = settings
        self._db: Session = db
        self._main_config: dict = main_config

    def build(self):
        pass

