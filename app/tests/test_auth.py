from fastapi.testclient import TestClient
import pytest
from requests import Response

from app import models, schemas, crud
from app.schemas.filters import Filters


@pytest.mark.usefixtures("fixture_data")
class TestAuth:
    """
    Functional endpoint tests
    """
    def test_bk(self):
        filter_params = {
            "Afweging": "beleidskeuze1030"    
        }
        #result = crud.beleidskeuze.valid(filters=Filters(filter_params))
        result = crud.gebruiker.all()
        print("HARK LENGTH IS")
        print(len(result))
        assert result

