# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import os
import tempfile

import pytest
import pyodbc
from application import app
from datamodel import endpoints
from Tests.test_data import generate_data
from globals import db_connection_settings

@pytest.fixture()
def test_user_pass():
    """
    Provides the test user password (read from env)
    """
    test_pw = os.getenv('TEST_PASS')
    if not test_pw:
        pytest.fail('No test password defined')
    return test_pw

@pytest.fixture()
def test_user_identifier():
    """
    Provides the test user identifier (read from env)
    """
    test_id = os.getenv('TEST_MAIL')
    if not test_id:
        pytest.fail('No test mail defined')
    return test_id


@pytest.fixture()
def test_user_UUID():
    """
    Provides the test user identifier (read from env)
    """
    test_id = os.getenv('TEST_UUID')
    return test_id

@pytest.fixture
def client():
    """
    Provides access to the flask test_client
    """
    return app.test_client()

@pytest.fixture
def auth(client, test_user_identifier, test_user_pass):
    """
    Provides a valid auth token
    """
    resp = client.post(
        '/v0.1/login', json={'identifier': test_user_identifier, 'password': test_user_pass})
    if not resp.status_code == 200:
        pytest.fail(f'Unable to authenticate with API: {resp.get_json()}')
    return (resp.get_json()['identifier']['UUID'], resp.get_json()['access_token'])

@pytest.fixture(scope="module")
def cleanup():
    """
    Ensures the database is cleaned up after running tests
    """
    test_uuid = os.getenv('TEST_UUID')
    if not test_uuid:
        pytest.fail(f'TEST_UUID env variable not found')
    yield 
    with pyodbc.connect(db_connection_settings) as cn:
        cur = cn.cursor()
        for table in endpoints:
            cur.execute(f"DELETE FROM {table.write_schema.Meta.table} WHERE Created_By = ?", test_uuid)

@pytest.mark.parametrize('endpoint', endpoints, ids=(map(lambda ep: ep.slug, endpoints)))
def test_endpoints(client, test_user_UUID, auth, cleanup, endpoint):   
    list_ep = f"v0.1/{endpoint.slug}"
    
    response = client.get(list_ep)
    found = len(response.json)
    assert response.status_code == 200, f"Status code for GET on {list_ep} was {response.status_code}, should be 200."


    if not endpoint.write_schema.Meta.read_only:
        test_data = generate_data(endpoint.write_schema, user_UUID=test_user_UUID, excluded_prop='excluded_post')
            
        response = client.post(list_ep, json=test_data, headers = {'Authorization': f'Token {auth[1]}'})

        assert response.status_code == 201, f"Status code for POST on {list_ep} was {response.status_code}, should be 201. Body content: {response.json}"

        
        new_id = response.get_json()['ID']        
        
        response = client.get(list_ep)
        assert found + 1 == len(response.json), 'No new object after POST'
        
        response = client.patch(list_ep + '/' + str(new_id), json={'Begin_Geldigheid':'1994-11-23T10:00:00'}, headers={'Authorization': f'Token {auth[1]}'})
        assert response.status_code == 200, f'Status code for PATCH on {list_ep} was {response.status_code}, should be 200. Body contents: {response.json}'

        response = client.get(list_ep + '/' + str(new_id))
        assert response.json[0]['Begin_Geldigheid'] == '1994-11-23T10:00:00', 'Patch did not change object.'
        response = client.get(list_ep)
        assert found + 1 == len(response.json), "New object after PATCH"