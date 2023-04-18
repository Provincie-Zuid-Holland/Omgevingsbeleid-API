from abc import ABC, abstractmethod
from sqlalchemy.orm import Session


class FixtureDataFactory(ABC):
    def __init__(self, db: Session):
        self._db = db
        self.objects = []

    @abstractmethod
    def populate_db(self):
        """
        Should commit all objects to DB.
        """

    @abstractmethod
    def create_all_objects(self):
        """
        Should instantiate all test objects, without db committing.
        """

    @abstractmethod
    def _create_object(self, data):
        """
        Should create a object instance and add to the factory list
        """

    @abstractmethod
    def _data(self):
        """
        Flat dict data of fixture objects, useful in unit tests
        """
