# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import os
import tempfile

import pytest
import pyodbc
from application import app
from datamodel import endpoints
from Tests.test_data import generate_data, reference_rich_beleidskeuze
from globals import db_connection_settings
from Endpoints.references import UUID_List_Reference

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
            new_uuids = list(cur.execute(f"SELECT UUID FROM {table.Meta.table} WHERE Created_By = ?", test_uuid))
            for field, ref in table.Meta.references.items():
                    # Remove all references first
                    if type(ref) == UUID_List_Reference:
                        for new_uuid in list(new_uuids):        
                            cur.execute(f"DELETE FROM {ref.link_tablename} WHERE {ref.my_col} = ?", new_uuid[0])    
            cur.execute(f"DELETE FROM {table.Meta.table} WHERE Created_By = ?", test_uuid)

@pytest.mark.parametrize('endpoint', endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints)))
def test_endpoints(client, test_user_UUID, auth, cleanup, endpoint):   
    
    list_ep = f"v0.1/{endpoint.Meta.slug}"
    response = client.get(list_ep)
    found = len(response.json)
    assert response.status_code == 200, f"Status code for GET on {list_ep} was {response.status_code}, should be 200."

    t_uuid = response.json[0]['UUID']
    version_ep = f"v0.1/version/{endpoint.Meta.slug}/{t_uuid}"
    response = client.get(version_ep)
    assert response.status_code == 200, f"Status code for GET on {version_ep} was {response.status_code}, should be 200."

    if not endpoint.Meta.read_only:
        test_data = generate_data(endpoint, user_UUID=test_user_UUID, excluded_prop='excluded_post')

        response = client.post(list_ep, json=test_data, headers = {'Authorization': f'Bearer {auth[1]}'})

        assert response.status_code == 201, f"Status code for POST on {list_ep} was {response.status_code}, should be 201. Body content: {response.json}"

        new_id = response.get_json()['ID']        
        
        response = client.get(list_ep)
        assert found + 1 == len(response.json), 'No new object after POST'
        
        response = client.patch(list_ep + '/' + str(new_id), json={'Begin_Geldigheid':'1994-11-23T10:00:00'}, headers={'Authorization': f'Bearer {auth[1]}'})
        assert response.status_code == 200, f'Status code for PATCH on {list_ep} was {response.status_code}, should be 200. Body contents: {response.json}'

        response = client.get(list_ep + '/' + str(new_id))
        assert response.json[0]['Begin_Geldigheid'] == '1994-11-23T10:00:00', 'Patch did not change object.'
        response = client.get(list_ep)
        assert found + 1 == len(response.json), "New object after PATCH"

def test_references(client, test_user_UUID, auth, cleanup):
    ep = f"v0.1/beleidskeuzes"
    response = client.post(ep, json=reference_rich_beleidskeuze, headers = {'Authorization': f'Bearer {auth[1]}'})
    
    assert response.status_code == 201, f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    new_id = response.get_json()['ID'] 
    ep = f"v0.1/beleidskeuzes/{new_id}"
    response = client.get(ep)
    assert response.status_code == 200, 'Could not get refered object'
    assert len(response.get_json()[0]['Ambities']) == 2 , 'References not retrieved'

    response = client.patch(ep, json={'Titel': 'Changed Title TEST'}, headers = {'Authorization': f'Bearer {auth[1]}'})
    assert response.status_code == 200, 'Patch failed'
    assert response.get_json()['Titel'] == 'Changed Title TEST' , 'Patch did not change title'
    assert len(response.get_json()['Ambities']) == 2 , 'Patch did not copy references'

def test_status_404(client, test_user_UUID, auth, cleanup):
    ep = f"v0.1/valid/ambities"
    response = client.get(ep)
    assert response.status_code == 404, 'This endpoint should not exist'

def test_status(client, test_user_UUID, auth, cleanup):
    ep = f"v0.1/valid/beleidskeuzes"
    response = client.get(ep)
    assert response.status_code != 404, 'This endpoint should exist'
    ids = []
    for _item in response.get_json():
        assert _item['Status'] == 'Vigerend'
        ids.append(_item['ID'])
    assert sorted(ids) == sorted(list(set(ids))), 'Double IDs in response that should only show valid objects per lineage'