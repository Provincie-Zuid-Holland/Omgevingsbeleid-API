import pytest

from Api.application import create_app
from Api.database import db as _db
from Api.settings import TestConfig

from Tests.Util.data_loader import FixtureLoader


@pytest.fixture(scope="class")
def app():
    _app = create_app(TestConfig)

    # with _app.app_context():
    #     _db.create_all()

    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.yield_fixture(scope="class")
def db(app):

    with app.app_context():
        _db.drop_all() # @todo: should not be here, but im lazy
        _db.create_all()

    _db._app = app

    yield _db

    _db.session.close()
    # _db.drop_all()


# With scope="class" this fixture will only be loaded once per class instead of for each test function
@pytest.fixture(scope="class")
def fixture_data(db):
    print("------------------- LOADING FIXTURE DATA ----------------------")

    loader = FixtureLoader(db)
    loader.load_fixtures()
    
    yield 1

    print("------------------- DESTROY FIXTURE DATA ----------------------")
    pass




