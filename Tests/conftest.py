import pytest
import pandas as pd

from Api.application import create_app
from Api.database import db as _db
from Api.settings import TestConfig


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
        _db.create_all()

    yield _db

    _db.session.close()
    # _db.drop_all()


# With scope="class" this fixture will only be loaded once per class instead of for each test function
@pytest.fixture(scope="class")
def fixture_data(db):
    print("------------------- LOADING FIXTURE DATA ----------------------")


    xls = pd.ExcelFile('./Tests/resources/fixtures/TestData_DiBe_2022-01-31.xlsx')
    print("\n\n\n")
    print(xls.sheet_names)
    print("\n\n\n")

    df1 = pd.read_excel(xls, 'Gebruikers')
    print(df1)

    print("\n\n\n")
    print(app)
    print("\n\n\n")

    df2 = pd.read_excel(xls, 'Beleidskeuzes')
    print(df2)

    yield 1

    print("------------------- DESTROY FIXTURE DATA ----------------------")
    pass




