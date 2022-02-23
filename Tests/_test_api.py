# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland


import os
import pytest
import pyodbc
import copy
import datetime
from flask import jsonify
from re import A

from Api.Models import (
    beleidskeuzes,
    ambities,
    beleidsrelaties,
    maatregelen,
    belangen,
    beleidsprestaties,
    beleidsmodule,
)
from Api.settings import null_uuid
from Api.datamodel import endpoints
from Api.settings import min_datetime, max_datetime
from Endpoints.references import (
    UUID_List_Reference,
)

from Api.Tests.test_data import generate_data, reference_rich_beleidskeuze


@pytest.fixture
def client():
    """
    Provides access to the flask test_client
    """
    return app.test_client()


@pytest.fixture
def auth(client):
    """
    Provides a valid auth token
    """
    test_id = os.getenv("TEST_MAIL")
    test_pw = os.getenv("TEST_PASS")
    resp = client.post("/v0.1/login", json={"identifier": test_id, "password": test_pw})
    if not resp.status_code == 200:
        pytest.fail(f"Unable to authenticate with API: {resp.get_json()}")
    return (resp.get_json()["identifier"]["UUID"], resp.get_json()["access_token"])


@pytest.fixture(autouse=True)
def cleanup(auth):
    """
    Ensures the database is cleaned up after running tests
    """
    yield
    test_uuid = auth[0]
    with pyodbc.connect(DB_CONNECTION_SETTINGS) as cn:
        cur = cn.cursor()
        for table in endpoints:
            new_uuids = list(
                cur.execute(
                    f"SELECT UUID FROM {table.Meta.table} WHERE Created_By = ?",
                    test_uuid,
                )
            )
            for field, ref in table.Meta.references.items():
                # Remove all references first
                if type(ref) == UUID_List_Reference:
                    for new_uuid in list(new_uuids):
                        cur.execute(
                            f"DELETE FROM {ref.link_tablename} WHERE {ref.my_col} = ?",
                            new_uuid[0],
                        )
            cur.execute(
                f"DELETE FROM {table.Meta.table} WHERE Created_By = ?", test_uuid
            )


@pytest.mark.parametrize(
    "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
)
def test_endpoints(client, auth, endpoint):
    if endpoint.Meta.slug == "beleidsrelaties" or "beleidsmodules":
        return
    list_ep = f"v0.1/{endpoint.Meta.slug}"
    response = client.get(list_ep)
    found = len(response.json)
    assert (
        response.status_code == 200
    ), f"Status code for GET on {list_ep} was {response.status_code}, should be 200. Response body: {response.get_json()}"

    t_uuid = response.json[0]["UUID"]
    version_ep = f"v0.1/version/{endpoint.Meta.slug}/{t_uuid}"
    response = client.get(version_ep)
    assert (
        response.status_code == 200
    ), f"Status code for GET on {version_ep} was {response.status_code}, should be 200."

    valid_ep = f"v0.1/valid/{endpoint.Meta.slug}"
    response = client.get(valid_ep)
    assert (
        response.status_code == 200
    ), f"Status code for GET on {valid_ep} was {response.status_code}, should be 200."

    if not endpoint.Meta.read_only:
        test_data = generate_data(
            endpoint, user_UUID=auth[0], excluded_prop="excluded_post"
        )

        response = client.post(
            list_ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
        )

        assert (
            response.status_code == 201
        ), f"Status code for POST on {list_ep} was {response.status_code}, should be 201. Body content: {response.json}"

        new_id = response.get_json()["ID"]

        response = client.get(list_ep)
        assert found + 1 == len(response.json), "No new object after POST"

        response = client.patch(
            list_ep + "/" + str(new_id),
            json={"Begin_Geldigheid": "1994-11-23T10:00:00Z"},
            headers={"Authorization": f"Bearer {auth[1]}"},
        )
        assert (
            response.status_code == 200
        ), f"Status code for PATCH on {list_ep} was {response.status_code}, should be 200. Body contents: {response.json}"

        response = client.get(list_ep + "/" + str(new_id))
        assert (
            response.json[0]["Begin_Geldigheid"] == "1994-11-23T10:00:00Z"
        ), "Patch did not change object."
        response = client.get(list_ep)
        assert found + 1 == len(response.json), "New object after PATCH"


def test_special_endpoints(client):
    specials = [f"v0.1/search/geo?query={null_uuid},{null_uuid}"]
    for special in specials:
        response = client.get(special)
        assert response.status_code == 200


def test_modules(client, auth):
    response = client.post(
        "v0.1/beleidsmodules",
        json={"Titel": "Test"},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 201, f"Response: {response.get_json()}"

    response = client.get(
        "v0.1/beleidsmodules", headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert response.status_code == 200, f"Response: {response.get_json()}"
    assert len(response.get_json()) != 0
    assert "Maatregelen" in response.get_json()[0]

    response = client.get("v0.1/valid/beleidsmodules")
    assert response.status_code == 200, f"Response: {response.get_json()}"


def test_references(client, auth):
    ep = f"v0.1/beleidskeuzes"
    response = client.post(
        ep,
        json=reference_rich_beleidskeuze,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    new_id = response.get_json()["ID"]

    ep = f"v0.1/beleidskeuzes/{new_id}"
    response = client.get(ep)
    assert response.status_code == 200, f"Could not get object, {response.get_json()}"
    assert len(response.get_json()[0]["Ambities"]) == 2, "References not retrieved"

    response = client.patch(
        ep,
        json={"Titel": "Changed Title TEST"},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200, f"Body content: {response.json}"
    response = client.get(ep)
    assert (
        response.get_json()[0]["Titel"] == "Changed Title TEST"
    ), "Patch did not change title"
    assert len(response.get_json()[0]["Ambities"]) == 2, "Patch did not copy references"


def test_id_404(client):
    ep = f"v0.1/ambities/99999"
    response = client.get(ep)
    assert response.status_code == 404, "This endpoint should return 404"


def test_id_status_404(client):
    ep = f"v0.1/valid/beleidskeuzes/99999"
    response = client.get(ep)
    assert response.status_code == 404, "This endpoint should return 404"


def test_status(client):
    ep = f"v0.1/valid/beleidskeuzes"
    response = client.get(ep)
    assert response.status_code != 404, "This endpoint should exist"
    ids = []
    for _item in response.get_json():
        assert _item["Status"] == "Vigerend"
        ids.append(_item["ID"])
    assert sorted(ids) == sorted(
        list(set(ids))
    ), "Double IDs in response that should only show valid objects per lineage"


def test_valid_filter(client, auth):
    ep = f"v0.1/beleidskeuzes?all_filters=Status:Uitgecheckt"
    response = client.get(ep, headers={"Authorization": f"Bearer {auth[1]}"})
    assert response.status_code == 200
    for json_obj in response.get_json():
        assert json_obj["Status"] == "Uitgecheckt", "Filter not filtering"


def test_valid_multiple_filter(client, auth):
    response = client.get(
        "v0.1/beleidskeuzes", headers={"Authorization": f"Bearer {auth[1]}"}
    )
    target = response.get_json()[0]

    ep = (
        f"v0.1/beleidskeuzes?filters=Status:{target['Status']},Titel:{target['Titel']} "
    )
    response = client.get(ep, headers={"Authorization": f"Bearer {auth[1]}"})
    found = False
    for json_obj in response.get_json():
        if json_obj["UUID"] == target["UUID"]:
            found = True
    assert found, "Did not find the target when filtering"


def test_invalid_filter(client, auth):
    ep = f"v0.1/beleidskeuzes?all_filters=Invalid:not_valid"
    response = client.get(ep, headers={"Authorization": f"Bearer {auth[1]}"})
    assert response.status_code == 400, "This is an invalid request"


@pytest.mark.parametrize(
    "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
)
def test_pagination_limit(client, endpoint):
    ep = f"v0.1/{endpoint}?limit=10"
    response = client.get(ep)
    if response.get_json():
        assert len(response.get_json()) <= 10, "Does not limit amount of results"


@pytest.mark.parametrize(
    "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
)
def test_pagination_offset(client, endpoint):
    ep = f"v0.1/{endpoint}"
    response = client.get(ep)
    if response.get_json():
        total_count = len(response.get_json())
        response = client.get(f"v0.1/{endpoint}?offset=10")
        assert (
            len(response.get_json()) <= total_count - 10
        ), "Does not offset the results"


def test_null_begin_geldigheid(client, auth):
    ep = f"v0.1/beleidskeuzes"
    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    test_data["Begin_Geldigheid"] = None
    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    new_uuid = response.get_json()["UUID"]
    ep = f"v0.1/version/beleidskeuzes/{new_uuid}"
    response = client.get(ep)

    assert response.status_code == 200, "Could not get posted object"
    assert response.get_json()["Begin_Geldigheid"] == min_datetime.replace(
        tzinfo=datetime.timezone.utc
    ).isoformat().replace("+00:00", "Z"), "Should be min_datetime"


def test_null_eind_geldigheid(client, auth):
    ep = f"v0.1/beleidskeuzes"
    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    test_data["Eind_Geldigheid"] = None
    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    new_uuid = response.get_json()["UUID"]
    ep = f"v0.1/version/beleidskeuzes/{new_uuid}"
    response = client.get(ep)

    assert response.status_code == 200, "Could not get posted object"
    assert response.get_json()["Eind_Geldigheid"] == max_datetime.replace(
        tzinfo=datetime.timezone.utc
    ).isoformat().replace("+00:00", "Z"), "Should be min_datetime"


def test_empty_referencelists(client, auth):
    # Create a beleidskeuze
    ep = f"v0.1/beleidskeuzes"

    empty_reference_beleidskeuze = copy.deepcopy(reference_rich_beleidskeuze)
    empty_reference_beleidskeuze["Ambities"] = []

    response = client.post(
        ep,
        json=empty_reference_beleidskeuze,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    new_uuid = response.get_json()["UUID"]
    new_id = response.get_json()["ID"]

    ep = f"v0.1/version/beleidskeuzes/{new_uuid}"
    response = client.get(ep)
    assert response.status_code == 200, "Could not get posted object"
    assert response.get_json()["Ambities"] == [], "Ambities should be an empty list"

    ep = f"v0.1/ambities"

    amb = generate_data(
        ambities.Ambities_Schema, user_UUID=auth[0], excluded_prop="excluded_patch"
    )

    amb["Eind_Geldigheid"] = "9999-12-12T23:59:59Z"

    response = client.post(
        ep,
        json=amb,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    new_uuid = response.get_json()["UUID"]

    ep = f"v0.1/beleidskeuzes/{new_id}"
    response = client.patch(
        ep,
        json={"Ambities": [{"UUID": new_uuid}]},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert len(response.get_json()["Ambities"]) == 1
    response = client.patch(
        ep, json={"Ambities": []}, headers={"Authorization": f"Bearer {auth[1]}"}
    )

    assert len(response.get_json()["Ambities"]) == 0


def test_HTML_Validation(client, auth):
    ep = f"v0.1/ambities"
    evil_omschrijving = """<h1>Happy</h1><script>console.log('muhaha')</script>"""
    response = client.post(
        ep,
        json={"Titel": "Evil ambitie", "Omschrijving": evil_omschrijving},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 400
    ), f"Status code for POST on {ep} was {response.status_code}, should be 400. Body content: {response.json}"


def test_reverse_lookup(client, auth):
    """
    Test wether reverse lookups work and show the correct inlined objects
    """
    # Create a ambitie
    ambitie_data = generate_data(
        ambities.Ambities_Schema, user_UUID=auth[0], excluded_prop="excluded_post"
    )
    ambitie_data["Eind_Geldigheid"] = "9999-12-12T23:59:59Z"

    response = client.post(
        "v0.1/ambities",
        json=ambitie_data,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST was {response.status_code}, should be 201. Body content: {response.json}"
    assert (
        response.get_json()["Ref_Beleidskeuzes"] == []
    ), f"Reverse lookup not empty on post. Body content: {response.json}"

    ambitie_id = response.get_json()["ID"]
    ambitie_uuid = response.get_json()["UUID"]

    # Create a new Beleidskeuze
    beleidskeuze_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    # Set ambities
    beleidskeuze_data["Ambities"] = [
        {"UUID": ambitie_uuid, "Koppeling_Omschrijving": "Test description"}
    ]
    # Set status
    beleidskeuze_data["Status"] = "Vigerend"
    beleidskeuze_data["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    response = client.post(
        "v0.1/beleidskeuzes",
        json=beleidskeuze_data,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST was {response.status_code}, should be 201. Body content: {response.json}"
    assert (
        response.get_json()["Ambities"][0]["Object"]["UUID"] == ambitie_uuid
    ), f"Nested objects are not on object. Body content: {response.json}"

    beleidskeuze_id = response.get_json()["ID"]
    beleidskeuze_uuid = response.get_json()["UUID"]

    # Get the ambitie
    response = client.get(
        f"v0.1/ambities/{ambitie_id}", headers={"Authorization": f"Bearer {auth[1]}"}
    )

    assert (
        response.status_code == 200
    ), f"Status code for GET was {response.status_code}, should be 200. Body content: {response.json}"

    assert (
        len(response.get_json()[0]["Ref_Beleidskeuzes"]) == 1
    ), f"Wrong amount of objects in reverse lookup field. Lookup field: {response.get_json()[0]['Ref_Beleidskeuzes']}"

    assert (
        response.get_json()[0]["Ref_Beleidskeuzes"][0]["UUID"] == beleidskeuze_uuid
    ), f"Nested objects are not on object. Body content: {response.json}"

    # Add a new version to the lineage
    response = client.patch(
        f"v0.1/beleidskeuzes/{beleidskeuze_id}",
        json={"Titel": "New Title"},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 200
    ), f"Status code for POST was {response.status_code}, should be 200. Body content: {response.json}"
    assert (
        response.get_json()["Ambities"][0]["Object"]["UUID"] == ambitie_uuid
    ), f"Nested objects are not on object. Body content: {response.json}"

    beleidskeuze_latest_id = response.get_json()["ID"]
    beleidskeuze_latest_uuid = response.get_json()["UUID"]

    # Get the ambitie
    response = client.get(
        f"v0.1/ambities/{ambitie_id}", headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 200
    ), f"Status code for GET was {response.status_code}, should be 200. Body content: {response.json}"
    assert (
        len(response.get_json()[0]["Ref_Beleidskeuzes"]) == 1
    ), f"Too many objects in reverse lookup field. Lookup field: {response.get_json()[0]['Ref_Beleidskeuzes']}"
    assert (
        response.get_json()[0]["Ref_Beleidskeuzes"][0]["UUID"]
        == beleidskeuze_latest_uuid
    ), f"Nested objects are on object. Body content: {response.json}"


def test_non_copy_field(client, auth):
    ep = f"v0.1/beleidskeuzes"

    # create beleidskeuze lineage
    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    first_uuid = response.get_json()["UUID"]
    ep = f"v0.1/beleidskeuzes/{response.get_json()['ID']}"
    # Patch a new aanpassing_op field
    response = client.patch(
        ep,
        json={"Titel": "Patched", "Aanpassing_Op": first_uuid},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 200
    ), f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
    assert (
        response.get_json()["Aanpassing_Op"] == first_uuid
    ), "Aanpassing_Op not saved!"

    # Patch a different field, aanpassing_op should be null
    response = client.patch(
        ep,
        json={"Titel": "Patched twice"},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 200
    ), f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
    assert response.get_json()["Aanpassing_Op"] == None, "Aanpassing_Op was copied!"


def test_all_filters(client, auth):
    ep = f"v0.1/beleidskeuzes"

    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    test_data["Status"] = "Ontwerp PS"
    test_data["Titel"] = "First"

    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    test_data["Status"] = "Ontwerp PS"
    test_data["Titel"] = "Second"

    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    test_data["Status"] = "Vigerend"
    test_data["Titel"] = "Second"

    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    response = client.get(
        ep + "?all_filters=Status:Vigerend,Titel:Second",
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 200
    ), f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
    for obj in response.get_json():
        assert obj["Titel"] == "Second", 'Titel should be "Second"'
        assert obj["Status"] == "Vigerend", 'Status should be "Vigerend"'


def test_multiple_filters(client, auth):
    ep = f"v0.1/beleidskeuzes"

    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    test_data["Status"] = "Ontwerp PS"
    test_data["Afweging"] = "Test4325123$%"
    test_data["Titel"] = "Test4325123$%"
    test_data["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    test_data["Status"] = "Ontwerp GS"
    test_data["Afweging"] = "Test4325123$%"
    test_data["Titel"] = "Anders"
    test_data["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    test_data["Status"] = "Vigerend"
    test_data["Afweging"] = "Anders"
    test_data["Titel"] = "Test4325123$%"
    test_data["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    response = client.get(
        ep + "?any_filters=Titel:Test4325123$%,Afweging:Test4325123$%",
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert (
        response.status_code == 200
    ), f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
    assert (
        len(response.get_json()) == 3
    ), "This should return all objects that were created"


def test_clear_patch_fields_beleidskeuzes(client, auth):
    ep = f"v0.1/beleidskeuzes"
    test_data = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )

    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    new_id = response.get_json()["ID"]
    new_uuid = response.get_json()["UUID"]

    modify_data = {"Titel": "Nieuwe Titel", "Aanpassing_Op": new_uuid}
    patch_ep = ep + f"/{new_id}"
    response = client.patch(
        patch_ep, json=modify_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )

    assert (
        response.status_code == 200
    ), f"Status code for PATCH on {patch_ep} was {response.status_code}, should be 200. Body content: {response.json}"
    assert response.get_json()["Aanpassing_Op"] == new_uuid

    modify_data = {"Titel": "Nieuwere Titel"}
    response = client.patch(
        patch_ep, json=modify_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert response.get_json()["Aanpassing_Op"] == None


def test_clear_patch_fields_maatregelen(client, auth):
    ep = f"v0.1/maatregelen"
    test_data = generate_data(
        maatregelen.Maatregelen_Schema, user_UUID=auth[0], excluded_prop="excluded_post"
    )
    response = client.post(
        ep, json=test_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )

    assert (
        response.status_code == 201
    ), f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

    new_id = response.get_json()["ID"]
    new_uuid = response.get_json()["UUID"]

    modify_data = {"Titel": "Nieuwe Titel", "Aanpassing_Op": new_uuid}
    patch_ep = ep + f"/{new_id}"
    response = client.patch(
        patch_ep, json=modify_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )

    assert (
        response.status_code == 200
    ), f"Status code for PATCH on {patch_ep} was {response.status_code}, should be 200. Body content: {response.json}"
    assert response.get_json()["Aanpassing_Op"] == new_uuid

    modify_data = {"Titel": "Nieuwere Titel"}
    response = client.patch(
        patch_ep, json=modify_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert response.get_json()["Aanpassing_Op"] == None


def test_graph_ep(client, auth):
    ep = f"v0.1/graph"
    response = client.get(ep, headers={"Authorization": f"Bearer {auth[1]}"})
    assert response.status_code == 200, "Graph endpoint not working"

    response = client.get(ep)
    assert response.status_code == 200, "Graph endpoint is unavailable without auth"


def test_null_date(client, auth):
    ep = f"v0.1/beleidsprestaties"
    bp_data = generate_data(
        beleidsprestaties.Beleidsprestaties_Schema,
        user_UUID=auth[0],
        excluded_prop="excluded_post",
    )
    response = client.post(
        ep, json=bp_data, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    bp_ID = response.get_json()["ID"]

    response = client.patch(
        ep + f"/{bp_ID}",
        json={"Eind_Geldigheid": None},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200, "patch failed"

    response = client.get(
        ep + f"/{bp_ID}", headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert response.get_json()[0]["Eind_Geldigheid"] == "9999-12-31T23:59:59Z"


def test_graph_normal(client, auth):
    # Create Ambitie
    test_amb = generate_data(ambities.Ambities_Schema, excluded_prop="excluded_post")
    test_amb["Eind_Geldigheid"] = "2992-11-23T10:00:00"
    amb_resp = client.post(
        "v0.1/ambities", json=test_amb, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    amb_UUID = amb_resp.get_json()["UUID"]

    # Create Belang
    test_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
    test_belang["Eind_Geldigheid"] = "2992-11-23T10:00:00"
    belang_resp = client.post(
        "v0.1/belangen",
        json=test_belang,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    belang_UUID = belang_resp.get_json()["UUID"]

    # Create Belang that is not valid anymore
    test_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
    belang_resp = client.post(
        "v0.1/belangen",
        json=test_belang,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    invalid_belang_UUID = belang_resp.get_json()["UUID"]

    # Create beleidskeuze (add objects)
    test_bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    test_bk["Eind_Geldigheid"] = "2992-11-23T10:00:00"
    test_bk["Ambities"] = [{"UUID": amb_UUID, "Koppeling_Omschrijving": ""}]
    test_bk["Belangen"] = [
        {"UUID": belang_UUID, "Koppeling_Omschrijving": ""},
        {"UUID": invalid_belang_UUID, "Koppeling_Omschrijving": ""},
    ]
    test_bk["Status"] = "Vigerend"
    response = client.post(
        "v0.1/beleidskeuzes",
        json=test_bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    bk_uuid = response.get_json()["UUID"]

    # Do Check
    response = client.get("v0.1/graph", headers={"Authorization": f"Bearer {auth[1]}"})
    graph_links = response.get_json()["links"]
    graph_nodes = response.get_json()["nodes"]
    found_links = []

    for link in graph_links:
        if link["source"] == bk_uuid:
            found_links.append(link["target"])
    assert len(found_links) == 2, "Not all links retrieved"
    assert belang_UUID in found_links, "Belang not retrieved"
    assert not invalid_belang_UUID in found_links, "Invalid belang retrieved"
    assert amb_UUID in found_links, "Ambitie not retrieved"
    assert set([amb_UUID, belang_UUID]) == set(
        found_links
    ), "Unexpected result for links"


def test_module_UUID(client, auth):
    # Create beleidskeuze (add objects)
    test_bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    response = client.post(
        "v0.1/beleidskeuzes",
        json=test_bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    new_uuid = response.get_json()["UUID"]
    new_id = response.get_json()["ID"]

    # Create Module
    test_module = generate_data(
        beleidsmodule.Beleidsmodule_Schema, excluded_prop="excluded_post"
    )

    test_module["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    test_module["Beleidskeuzes"] = [{"UUID": new_uuid, "Koppeling_Omschrijving": ""}]

    response = client.post(
        "v0.1/beleidsmodules",
        json=test_module,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 201
    module_uuid = response.get_json()["UUID"]

    # Check reverse
    response = client.get(f"v0.1/beleidskeuzes/{new_id}")
    assert response.status_code == 200

    assert response.get_json()[0]["Ref_Beleidsmodules"][0]["UUID"] == module_uuid

    # Add new version to bk
    response = client.patch(
        f"v0.1/beleidskeuzes/{new_id}",
        json={"Titel": "Nieuwe Titel"},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    # Check reverse again
    response = client.get(f"v0.1/beleidskeuzes/{new_id}")
    assert response.status_code == 200
    assert not (response.get_json()[0]["Ref_Beleidsmodules"]), "Should not be in module"


def test_maatregelen_link(client, auth):
    # Create Maatregel
    test_ma = generate_data(
        maatregelen.Maatregelen_Schema, excluded_prop="excluded_post"
    )
    test_ma["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    test_ma["Status"] = "Vigerend"

    response = client.post(
        "v0.1/maatregelen", json=test_ma, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    ma_uuid = response.get_json()["UUID"]

    # Create beleidskeuze (add objects)
    test_bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    test_bk["Maatregelen"] = [{"UUID": ma_uuid, "Koppeling_Omschrijving": "Test"}]
    response = client.post(
        "v0.1/beleidskeuzes",
        json=test_bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    bk_id = response.get_json()["ID"]

    # Check beleidskeuze
    response = client.get(
        f"v0.1/beleidskeuzes/{bk_id}",
        json=test_bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.get_json()[0]["Maatregelen"], "references where empty"
    assert (
        response.get_json()[0]["Maatregelen"][0]["Object"]["UUID"] == ma_uuid
    ), "Maatregel not linked"


def test_valid(client, auth):
    # Create Belang
    old_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
    old_belang["Eind_Geldigheid"] = "1992-11-23T10:00:00"
    new_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
    new_belang["Eind_Geldigheid"] = "2992-11-23T10:00:00"

    response = client.post(
        "v0.1/belangen", json=old_belang, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    old_belang_uuid = response.get_json()["UUID"]

    response = client.post(
        "v0.1/belangen", json=new_belang, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    new_belang_uuid = response.get_json()["UUID"]

    response = client.get("v0.1/valid/belangen")
    found_new = False
    for belang in response.get_json():
        assert belang["UUID"] != old_belang_uuid
        if belang["UUID"] == new_belang_uuid:
            found_new = True
    assert found_new


def test_protect_invalid(client, auth):
    response = client.get("v0.1/belangen")
    assert response.status_code == 401, f"body: {response.get_json()}"

    response = client.get(
        "v0.1/belangen", headers={"Authorization": f"Bearer {auth[1]}"}
    )
    assert response.status_code == 200

    response = client.get("v0.1/valid/belangen")
    assert response.status_code == 200


def test_filter(client, auth):
    response = client.get(
        f"v0.1/beleidsmodules?any_filters=Created_By:{auth[0]}",
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200


def test_non_valid_reference(client, auth):
    # Create Maatregel
    test_ma = generate_data(
        maatregelen.Maatregelen_Schema, excluded_prop="excluded_post"
    )
    test_ma["Status"] = "Ontwerp GS Concept"
    response = client.post(
        "v0.1/maatregelen", json=test_ma, headers={"Authorization": f"Bearer {auth[1]}"}
    )
    ma_uuid = response.get_json()["UUID"]

    # Create beleidskeuze
    test_bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    test_bk["Status"] = "Ontwerp GS Concept"
    test_bk["Maatregelen"] = [{"UUID": ma_uuid, "Koppeling_Omschrijving": "Test"}]
    response = client.post(
        "v0.1/beleidskeuzes",
        json=test_bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    bk_id = response.get_json()["ID"]

    # Check beleidskeuze
    response = client.get(
        f"v0.1/beleidskeuzes/{bk_id}",
        json=test_bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert len(response.get_json()[0]["Maatregelen"]) == 1, "references should not be empty"


def test_graph_relation(client, auth):
    # Create BK1 & BK2 (valid)

    bk_1 = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )

    bk_2 = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )

    bk_1["Status"] = "Vigerend"
    bk_1["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk_1,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201, f"{response.get_json()}"
    bk_1_UUID = response.get_json()["UUID"]

    bk_2["Status"] = "Vigerend"
    bk_2["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk_2,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201, f"{response.get_json()}"
    bk_2_UUID = response.get_json()["UUID"]

    # Check if bks are in valid view
    get_r = client.get('v0.1/valid/beleidskeuzes')
    assert bk_1_UUID in (map(lambda bk: bk['UUID'],get_r.get_json()))
    assert bk_2_UUID in (map(lambda bk: bk['UUID'],get_r.get_json()))

    br = generate_data(
        beleidsrelaties.Beleidsrelaties_Schema, excluded_prop="excluded_post"
    )
    br["Status"] = "Akkoord"
    br["Van_Beleidskeuze"] = bk_1_UUID
    br["Naar_Beleidskeuze"] = bk_2_UUID
    br["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidsrelaties",
        json=br,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 201, f"{response.get_json()}"
    br_id = response.get_json()['ID']
    br_uuid = response.get_json()['UUID']

    get_r = client.get('v0.1/valid/beleidsrelaties')
    assert br_uuid in list((map(lambda br: br['UUID'], get_r.get_json())))
    


    # Check graph
    response = client.get("v0.1/graph")
    links = response.get_json()["links"]
    found_1, found_2 = False, False
    for node in response.get_json()["nodes"]:
        if node["UUID"] == bk_1_UUID:
            found_1 = True
        if node["UUID"] == bk_2_UUID:
            found_2 = True

    assert found_1
    assert found_2
    
    assert {"source": bk_1_UUID, "target": bk_2_UUID, "type": "Relatie"} in links


def test_reverse_valid_check(client, auth):
    amb = generate_data(ambities.Ambities_Schema, excluded_prop="excluded_post")

    response = client.post(
        "v0.1/ambities",
        json=amb,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 201
    assert (
        response.get_json()["Ref_Beleidskeuzes"] == []
    ), "should be empty because nothing refers to this"

    amb_uuid = response.get_json()["UUID"]

    bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk["Status"] = "Ontwerp GS Concept"
    bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    bk["Ambities"] = [{"UUID": amb_uuid, "Koppeling_Omschrijving": ""}]

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert (
        response.status_code == 201
    ), f"Failed to create beleidskeuze: {response.get_json()}"

    response = client.get(f"v0.1/version/ambities/{amb_uuid}")
    assert (
        response.get_json()["Ref_Beleidskeuzes"] == []
    ), "should be empty because beleidskeuze is not valid"
    assert response.status_code == 200, f"Failed to get ambitie: {response.get_json()}"


def test_future_links(client, auth):
    amb = generate_data(ambities.Ambities_Schema, excluded_prop="excluded_post")

    future = datetime.datetime.now() + datetime.timedelta(days=2)

    amb["Begin_Geldigheid"] = future.strftime("%Y-%m-%dT%H:%M:%SZ")
    amb["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    response = client.post(
        "v0.1/ambities",
        json=amb,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 201

    assert (
        response.get_json()["Ref_Beleidskeuzes"] == []
    ), "should be empty because nothing refers to this"

    amb_uuid = response.get_json()["UUID"]

    response = client.get(
        "v0.1/valid/ambities",
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert amb_uuid not in map(lambda ob: ob.get("UUID"), response.get_json())

    bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )

    bk["Status"] = "Vigerend"
    bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    bk["Ambities"] = [{"UUID": amb_uuid}]

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201
    assert response.get_json()["Ambities"] == [], "Ambitie is not yet valid"

    bk_uuid = response.get_json()["UUID"]

    response = client.get(f"v0.1/version/beleidskeuzes/{bk_uuid}")

    assert response.get_json()["Ambities"] == [], "Ambitie is not yet valid"


def test_latest_version(client, auth):
    bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk["Status"] = "Ontwerp GS Concept"
    bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201
    bk_ID = response.get_json()["ID"]
    bk_UUID = response.get_json()["UUID"]

    bk["Status"] = "Ontwerp PS"
    response = client.patch(
        f"v0.1/beleidskeuzes/{bk_ID}",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200
    new_bk_UUID = response.get_json()["UUID"]

    response = client.get(f"v0.1/version/beleidskeuzes/{bk_UUID}")
    assert response.status_code == 200
    assert response.get_json()["Latest_Version"] == new_bk_UUID
    assert response.get_json()["Latest_Status"] == "Ontwerp PS"


def test_effective_version(client, auth):
    bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk["Status"] = "Vigerend"
    bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201
    bk_ID = response.get_json()["ID"]
    bk_UUID = response.get_json()["UUID"]

    bk["Status"] = "Ontwerp PS"
    response = client.patch(
        f"v0.1/beleidskeuzes/{bk_ID}",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200
    new_bk_UUID = response.get_json()["UUID"]

    response = client.get(f"v0.1/version/beleidskeuzes/{new_bk_UUID}")
    assert response.status_code == 200
    assert response.get_json()["Effective_Version"] == bk_UUID

def test_ID_relations_valid(client, auth):
    # Create two beleidskeuzes
    bk_a = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk_a["Status"] = "Vigerend"
    bk_a["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response_a = client.post(
        "v0.1/beleidskeuzes",
        json=bk_a,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    a_uuid = response_a.get_json()['UUID']    
    a_id = response_a.get_json()['ID']    

    bk_b = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk_b["Status"] = "Vigerend"
    bk_b["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response_b = client.post(
        "v0.1/beleidskeuzes",
        json=bk_b,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    b_uuid = response_b.get_json()['UUID']    
    b_id = response_b.get_json()['ID']

    # Create a beleidsrelatie
    br = generate_data(
        beleidsrelaties.Beleidsrelaties_Schema, excluded_prop="excluded_post"
    )
    br['Status'] = 'Akkoord'
    br['Van_Beleidskeuze'] = a_uuid
    br['Naar_Beleidskeuze'] = b_uuid
    br['Eind_Geldigheid'] = "9999-12-31T23:59:59Z"
    response_br = client.post(
        "v0.1/beleidsrelaties",
        json=br,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    
    assert response_br.status_code == 201
    br_uuid = response_br.get_json()['UUID']
    br_id = response_br.get_json()['ID']

    response_get_br = client.get(
        f"v0.1/beleidsrelaties/{br_id}"
    )

    assert response_get_br.status_code == 200
    assert response_br.get_json()['Van_Beleidskeuze']['UUID'] == a_uuid
    assert response_br.get_json()['Naar_Beleidskeuze']['UUID'] == b_uuid

    # Update beleidskeuze b
    response_patch_b = client.patch(
        f"v0.1/beleidskeuzes/{b_id}",
        json={**bk_b, 'Titel':'SWEN'},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    b_patch_uuid = response_patch_b.get_json()['UUID']    

    response_get_br = client.get(
        f"v0.1/beleidsrelaties/{br_id}"
    )

    assert response_get_br.status_code == 200
    # Expect the new beleidskeuze to show    
    assert response_get_br.get_json()[0]['Van_Beleidskeuze']['UUID'] == a_uuid
    assert response_get_br.get_json()[0]['Naar_Beleidskeuze']['UUID'] == b_patch_uuid


    # Also check the single version
    response_get_br_ver = client.get(
        f"v0.1/version/beleidsrelaties/{br_uuid}")
    
    assert response_get_br_ver.status_code == 200
    assert response_get_br_ver.get_json()['Van_Beleidskeuze']['UUID'] == a_uuid
    assert response_get_br_ver.get_json()['Naar_Beleidskeuze']['UUID'] == b_patch_uuid
    
    # Check BR in valid view
    response_get_br_valid = client.get(
        f"v0.1/valid/beleidsrelaties")

    assert br_uuid in (map(lambda br: br['UUID'], response_get_br_valid.get_json()))


def test_ID_relations_full(client, auth):
    # Create two beleidskeuzes
    bk_a = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk_a["Status"] = "Vigerend"
    bk_a["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response_a = client.post(
        "v0.1/beleidskeuzes",
        json=bk_a,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    a_uuid = response_a.get_json()['UUID']    
    a_id = response_a.get_json()['ID']    

    bk_b = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk_b["Status"] = "Vigerend"
    bk_b["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response_b = client.post(
        "v0.1/beleidskeuzes",
        json=bk_b,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    b_uuid = response_b.get_json()['UUID']    
    b_id = response_b.get_json()['ID']

    # Create a beleidsrelatie
    br = generate_data(
        beleidsrelaties.Beleidsrelaties_Schema, excluded_prop="excluded_post"
    )
    br['Status'] = 'Akkoord'
    br['Van_Beleidskeuze'] = a_uuid
    br['Naar_Beleidskeuze'] = b_uuid
    br['Eind_Geldigheid'] = "9999-12-31T23:59:59Z"
    response_br = client.post(
        "v0.1/beleidsrelaties",
        json=br,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    
    assert response_br.status_code == 201
    br_uuid = response_br.get_json()['UUID']
    br_id = response_br.get_json()['ID']

    response_get_br = client.get(
        f"v0.1/beleidsrelaties/{br_id}"
    )

    assert response_get_br.status_code == 200
    assert response_br.get_json()['Van_Beleidskeuze']['UUID'] == a_uuid
    assert response_br.get_json()['Naar_Beleidskeuze']['UUID'] == b_uuid

    # Update beleidskeuze b
    response_patch_b = client.patch(
        f"v0.1/beleidskeuzes/{b_id}",
        json={**bk_b, 'Titel':'SWEN', 'Status':'Ontwerp GS'},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    b_patch_uuid = response_patch_b.get_json()['UUID']    

    all_response = client.get(f"v0.1/beleidsrelaties", headers={"Authorization": f"Bearer {auth[1]}"})
    valid_response = client.get(f"v0.1/valid/beleidsrelaties")

    assert all_response.status_code == 200
    assert valid_response.status_code == 200

    # Check if we see the valid version in valid
    for relation in valid_response.get_json():
        if relation['ID'] == br_id:
            assert relation['Van_Beleidskeuze']['UUID'] == a_uuid
            assert relation['Naar_Beleidskeuze']['UUID'] == b_uuid
    
    for relation in all_response.get_json():
        if relation['ID'] == br_id:
            assert relation['Van_Beleidskeuze']['UUID'] == a_uuid
            assert relation['Naar_Beleidskeuze']['UUID'] == b_patch_uuid

def test_edits_200(client, auth):
    response = client.get('v0.1/edits')
    assert response.status_code == 200

def test_edits_latest(client, auth):
    bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    bk_uuid = response.get_json()['UUID']

    response = client.get('v0.1/edits')
    assert response.status_code == 200
    assert response.get_json()[0]['UUID'] == bk_uuid


def test_edits_vigerend(client, auth):
    bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    bk_uuid = response.get_json()['UUID']
    bk_id = response.get_json()['ID']

    response = client.patch(
        f"v0.1/beleidskeuzes/{bk_id}",
        json={'Status':'Vigerend'},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    response = client.get('v0.1/edits')
    assert response.status_code == 200
    for row in response.get_json():
        assert row['ID'] != bk_id 

def test_empty_edit(client, auth):
    bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk["Status"] = "Vigerend"
    bk["Eind_Geldigheid"] = "9999-12-31T23:59:59"

    # print(bk)

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201
    bk_ID = response.get_json()["ID"]
    bk_UUID = response.get_json()["UUID"]

    # Patch without changes
    response = client.patch(
        f"v0.1/beleidskeuzes/{bk_ID}",
        json=bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.get_json()['UUID'] == bk_UUID


def test_module_concept(client, auth):
    """A module should show non-effective objects
    """
    # Create non effective beleidskeuze
    test_bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )

    test_bk['Status'] = 'Ontwerp GS'
    test_bk['Begin_Geldigheid'] = "1900-12-31T23:59:59Z"
    test_bk['Eind_Geldigheid'] = "9999-12-31T23:59:59Z"
    response = client.post(
        "v0.1/beleidskeuzes",
        json=test_bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    bk_uuid = response.get_json()["UUID"]
    bk_id = response.get_json()["ID"]

    # Create Module
    test_module = generate_data(
        beleidsmodule.Beleidsmodule_Schema, excluded_prop="excluded_post"
    )

    test_module["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    test_module["Beleidskeuzes"] = [{"UUID": bk_uuid, "Koppeling_Omschrijving": ""}]

    response = client.post(
        "v0.1/beleidsmodules",
        json=test_module,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 201
    module_uuid = response.get_json()["UUID"]
    module_id = response.get_json()["ID"]

    # Check module
    response = client.get(f"v0.1/beleidsmodules/{module_id}")
    assert response.status_code == 200

    assert len(response.get_json()[0]["Beleidskeuzes"]) == 1
    assert response.get_json()[0]["Beleidskeuzes"][0]['Object']["UUID"] == bk_uuid


def test_module_multiple_concept(client, auth):
    """A module should show non-effective objects
    """
    # Create non effective beleidskeuze
    test_bk = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )

    test_bk['Status'] = 'Ontwerp GS'
    test_bk['Begin_Geldigheid'] = "1900-12-31T23:59:59Z"
    test_bk['Eind_Geldigheid'] = "9999-12-31T23:59:59Z"
    response = client.post(
        "v0.1/beleidskeuzes",
        json=test_bk,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    bk_uuid = response.get_json()["UUID"]
    bk_id = response.get_json()["ID"]

    # Create Module
    test_module = generate_data(
        beleidsmodule.Beleidsmodule_Schema, excluded_prop="excluded_post"
    )

    test_module["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
    test_module["Beleidskeuzes"] = [{"UUID": bk_uuid, "Koppeling_Omschrijving": ""}]

    response = client.post(
        "v0.1/beleidsmodules",
        json=test_module,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 201
    module_uuid = response.get_json()["UUID"]
    module_id = response.get_json()["ID"]

    # Check module
    response = client.get(f"v0.1/beleidsmodules/{module_id}")
    assert response.status_code == 200

    assert len(response.get_json()[0]["Beleidskeuzes"]) == 1
    assert response.get_json()[0]["Beleidskeuzes"][0]['Object']["UUID"] == bk_uuid

    # Create non effective maatregel
    test_ma = generate_data(
        maatregelen.Maatregelen_Schema, excluded_prop="excluded_post"
    )

    test_ma['Status'] = 'Ontwerp GS'
    test_ma['Begin_Geldigheid'] = "1900-12-31T23:59:59Z"
    test_ma['Eind_Geldigheid'] = "9999-12-31T23:59:59Z"
    response = client.post(
        "v0.1/maatregelen",
        json=test_ma,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    ma_uuid = response.get_json()["UUID"]
    ma_id = response.get_json()["ID"]

    response = client.patch(
        f"v0.1/beleidsmodules/{module_id}",
        json={'Maatregelen': [{"UUID": ma_uuid, "Koppeling_Omschrijving": ""}]},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 200

    
    # Check module
    response = client.get(f"v0.1/beleidsmodules/{module_id}")
    assert response.status_code == 200

    assert len(response.get_json()[0]["Beleidskeuzes"]) == 1
    assert len(response.get_json()[0]["Maatregelen"]) == 1
    assert response.get_json()[0]["Beleidskeuzes"][0]['Object']["UUID"] == bk_uuid
    assert response.get_json()[0]["Maatregelen"][0]['Object']["UUID"] == ma_uuid


def test_latest_middle(client, auth):
    bk1 = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk1["Status"] = "Ontwerp GS Concept"
    bk1["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk1,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201
    bk_ID = response.get_json()["ID"]
    bk1_UUID = response.get_json()["UUID"]

    bk_2 = {**bk1, 'Status':['Ontwerp GS']}

    response = client.patch(
        f"v0.1/beleidskeuzes/{bk_ID}",
        json={'Status':'Ontwerp GS'},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200, response.get_json()
    bk2_UUID = response.get_json()["UUID"]

    # Check if latest version matches
    response = client.get(f"v0.1/version/beleidskeuzes/{bk1_UUID}")
    assert response.status_code == 200
    assert response.get_json()["Latest_Version"] == bk2_UUID
    assert response.get_json()["Latest_Status"] == "Ontwerp GS"

    response = client.patch(
        f"v0.1/beleidskeuzes/{bk_ID}",
        json={'Status':'Vigerend', 'Begin_Geldigheid':"2010-12-31T23:59:59Z", 'Eind_Geldigheid':"2011-12-31T23:59:59Z" },
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200
    bk3_UUID = response.get_json()["UUID"]

    # Check if latest version matches
    response = client.get(f"v0.1/version/beleidskeuzes/{bk1_UUID}")
    assert response.status_code == 200
    assert response.get_json()["Latest_Version"] == bk3_UUID
    assert response.get_json()["Latest_Status"] == "Vigerend"

    
    # Check if latest version matches
    response = client.get(f"v0.1/version/beleidskeuzes/{bk2_UUID}")
    assert response.status_code == 200
    assert response.get_json()["Latest_Version"] == bk3_UUID
    assert response.get_json()["Latest_Status"] == "Vigerend"


def test_self_effective_version(client, auth):
    bk1 = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk1["Status"] = "Vigerend"
    bk1["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk1,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201
    bk1_UUID = response.get_json()["UUID"]
    bk_ID = response.get_json()["ID"]

    # Check if latest version matches
    response = client.get(f"v0.1/version/beleidskeuzes/{bk1_UUID}")
    assert response.status_code == 200
    assert response.get_json()["Effective_Version"] == bk1_UUID
    
    # Make new version
    response = client.patch(
        f"v0.1/beleidskeuzes/{bk_ID}",
        json={'Status':'Ontwerp GS'},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200

    # Check if latest version matches
    response = client.get(f"v0.1/version/beleidskeuzes/{bk1_UUID}")
    assert response.status_code == 200
    assert response.get_json()["Effective_Version"] == bk1_UUID


def test_effective_in_edits(client, auth):
    bk1 = generate_data(
        beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    )
    bk1["Status"] = "Vigerend"
    bk1["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

    response = client.post(
        "v0.1/beleidskeuzes",
        json=bk1,
        headers={"Authorization": f"Bearer {auth[1]}"},
    )

    assert response.status_code == 201
    bk1_UUID = response.get_json()["UUID"]
    bk_ID = response.get_json()["ID"]
    
    # Make new version
    response = client.patch(
        f"v0.1/beleidskeuzes/{bk_ID}",
        json={'Status':'Ontwerp GS'},
        headers={"Authorization": f"Bearer {auth[1]}"},
    )
    assert response.status_code == 200
    bk2_uuid = response.get_json()['UUID']
    
    # Check if the effective version shows up in edits
    response = client.get(f"v0.1/edits")
    assert response.status_code == 200
    found = False
    effective_correct = False
    for edit in response.get_json():
        if edit['Type'] == 'beleidskeuzes':
            if edit['UUID'] == bk2_uuid:
                if edit['Effective_Version'] == bk1_UUID:
                    effective_correct = True
                found = True
                break
            
    assert(found)
    assert(effective_correct)