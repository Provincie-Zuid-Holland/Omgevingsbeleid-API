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
