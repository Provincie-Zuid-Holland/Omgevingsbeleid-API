# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

"""
Tests that check wether the generated OpenAPI specification is valid
"""
from openapi_spec_validator import openapi_v3_spec_validator, validate_spec
import os
import tempfile

import pytest

from application import app

@pytest.fixture
def client():
    return app.test_client()

def test_spec(client):
    """Check wether the spec endpoint is valid and available"""
    spec_url = f"v0.1/spec"
    response = client.get(spec_url)
    assert response.status_code == 200, 'Spec should be available'
    assert list(openapi_v3_spec_validator.iter_errors(response.get_json())) == [], 'Spec should pass validation'
