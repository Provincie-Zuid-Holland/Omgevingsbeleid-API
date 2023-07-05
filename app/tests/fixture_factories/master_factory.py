from sqlalchemy.orm import Session

from .fixture_factory import FixtureDataFactory


class MasterFixtureFactory(FixtureDataFactory):
    """
    TODO: register all factories and execute individually to setup a
    full test DB
    """

    def __init__(self, db: Session):
        self._db = db
        self.objects = []

    def populate_db(self):
        """
        Should commit all objects to DB.
        """

    def create_all_objects(self):
        """
        Should instantiate all test objects, without db committing.
        """

    def _create_object(self, data):
        """
        Should create a object instance and add to the factory list
        """

    def _data(self):
        """
        Flat fict data of fixture objects, useful in unit tests
        """
