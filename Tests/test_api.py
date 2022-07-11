# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import base64
import pytest
from pprint import pprint
import datetime
import copy
import uuid

from Api.settings import null_uuid, min_datetime, max_datetime
from Api.datamodel import endpoints
from Tests.TestUtils.schema_data import generate_data, reference_rich_beleidsdoel
from Api.Models import (
    beleidskeuzes,
    ambities,
    beleidsrelaties,
    gebiedsprogrammas,
    maatregelen,
    belangen,
    beleidsprestaties,
    beleidsmodule,
)
from Api.Models.beleidskeuzes import Beleidskeuzes
from Api.Models.maatregelen import Maatregelen
from Api.Models.beleidsprestaties import Beleidsprestaties


@pytest.mark.usefixtures("fixture_data")
class TestApi:

    def test_beleidskeuze_valid_view_past_vigerend(self, client_admin):
        response = client_admin.get("v0.1/valid/beleidskeuzes?all_filters=Afweging:beleidskeuze1030")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.get_json()

        assert len(data) == 0, f"We are expecting nothing as the most recent Vigerend has its Eind_Geldigheid in the past"


    def test_beleidskeuze_valid_view_future_vigerend(self, client_admin):
        response = client_admin.get("v0.1/valid/beleidskeuzes?all_filters=Afweging:beleidskeuze1011")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.get_json()
        assert len(data) >= 1, f"Expecting at least 1 results"

        expected_uuids = set([
            "FEC2E000-0011-0017-0000-000000000000", # This is Vigerend and still in current date time range
        ])
        found_uuids = set([r["UUID"] for r in data])
        assert expected_uuids.issubset(found_uuids), f"Not all expected uuid where found"

        forbidden_uuids = set([
            "FEC2E000-0011-0011-0000-000000000000", # first version early status
            "FEC2E000-0011-0021-0000-000000000000", # second version early status
            "FEC2E000-0011-0027-0000-000000000000", # New version status Vigerend, but in the future
        ])
        intersect = found_uuids & forbidden_uuids
        assert len(intersect) == 0, f"Some forbidden uuid where found"


    def test_leden_excluded_from_graph(self, client, client_fred, fixture_data):
        _link_to3 = {"source": fixture_data._instances['keu:6'].UUID,
                "target":fixture_data._instances['ver:3'].UUID,
                "type":"Koppeling"}

        _link_to2 = {"source": fixture_data._instances['keu:6'].UUID,
                "target":fixture_data._instances['ver:2'].UUID,
                "type":"Koppeling"}

        response = client_fred.get("v0.1/graph")
        node_uuids = map(lambda node: node['UUID'], response.get_json()['nodes'])
        links = response.get_json()['links']
        # This is the source beleidskeuze
        assert fixture_data._instances['keu:6'].UUID in node_uuids

        # This one should show up (it has Type==Artikel)
        assert fixture_data._instances['ver:3'].UUID in node_uuids
        assert _link_to3 in links

        # This one should not show up (it has Type==Lid)
        assert fixture_data._instances['ver:2'].UUID not in node_uuids
        assert _link_to2 not in links

    def test_werkingsgebied_valid_view(self, client, client_fred):
        response = client_fred.get("v0.1/valid/werkingsgebieden")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.get_json()
        assert len(data) >= 2, f"Expecting at least 2 results"

        expected_uuids = set([
            "8EB1ED00-0002-2222-0000-000000000000",
            "8EB1ED00-0003-0000-0000-000000000000",
        ])
        found_uuids = set([r["UUID"] for r in data])
        assert expected_uuids.issubset(found_uuids), f"Not all expected uuid where found"

        forbidden_uuids = set([
            "8EB1ED00-0002-1111-0000-000000000000",
            "8EB1ED00-0004-0000-0000-000000000000",
            "8EB1ED00-0005-0000-0000-000000000000",
            "8EB1ED00-0006-0000-0000-000000000000",
            "8EB1ED00-0007-0000-0000-000000000000",
        ])
        intersect = found_uuids & forbidden_uuids
        assert len(intersect) == 0, f"Some forbidden uuid where found"


    def test_werkingsgebied_all_valid_view(self, db):
        query = "SELECT UUID FROM All_Valid_Werkingsgebieden"
        res = db.engine.execute(query)

        expected_uuids = set([
            "8EB1ED00-0002-1111-0000-000000000000",
            "8EB1ED00-0002-2222-0000-000000000000",
            "8EB1ED00-0003-0000-0000-000000000000",
            "8EB1ED00-0006-0000-0000-000000000000",
            "8EB1ED00-0007-0000-0000-000000000000",
        ])
        found_uuids = set([r["UUID"] for r in res])
        assert len(found_uuids) >= 4, f"Expecting at least 4 results"
        assert expected_uuids.issubset(found_uuids), f"Not all expected uuid where found"

        forbidden_uuids = set([
            "8EB1ED00-0004-0000-0000-000000000000",
            "8EB1ED00-0005-0000-0000-000000000000",
        ])
        intersect = found_uuids & forbidden_uuids
        assert len(intersect) == 0, f"Some forbidden uuid where found"


    def test_werkingsgebied_valid_lineage(self, client, client_fred):
        response = client_fred.get("v0.1/valid/werkingsgebieden/1000")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.get_json()
        
        expected_uuids = set([
            "8EB1ED00-0002-1111-0000-000000000000",
            "8EB1ED00-0002-2222-0000-000000000000",
        ])
        found_uuids = set([r["UUID"] for r in data])
        assert len(found_uuids) == 2, f"Expecting at 2 results"
        assert expected_uuids.issubset(found_uuids), f"Not all expected uuid where found"


    def test_modules(self, client_fred):
        response = client_fred.post("v0.1/beleidsmodules", json={"Titel": "Test"})
        assert response.status_code == 201, f"Response: {response.get_json()}"

        response = client_fred.get("v0.1/beleidsmodules")
        assert response.status_code == 200, f"Response: {response.get_json()}"
        assert len(response.get_json()) != 0
        assert "Maatregelen" in response.get_json()[0]

        response = client_fred.get("v0.1/valid/beleidsmodules")
        assert response.status_code == 200, f"Response: {response.get_json()}"


    def test_references(self, client_fred):
        ep = f"v0.1/beleidsdoelen"
        response = client_fred.post(ep, json=reference_rich_beleidsdoel)
        assert response.status_code == 201, f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

        new_id = response.get_json()["ID"]
        ep = f"v0.1/beleidsdoelen/{new_id}"
        response = client_fred.get(ep)
        assert response.status_code == 200, f"Could not get object, {response.get_json()}"
        assert len(response.get_json()[0]["Ambities"]) == 2, "References not retrieved"

        response = client_fred.patch(ep, json={"Titel": "Changed Title TEST"})
        assert response.status_code == 200, f"Body content: {response.json}"
        response = client_fred.get(ep)
        assert response.get_json()[0]["Titel"] == "Changed Title TEST", "Patch did not change title"
        assert len(response.get_json()[0]["Ambities"]) == 2, "Patch did not copy references"


    def test_id_404(self, client):
        ep = f"v0.1/ambities/99999"
        response = client.get(ep)
        assert response.status_code == 404, "This endpoint should return 404"


    def test_id_status_404(self, client):
        ep = f"v0.1/valid/beleidskeuzes/99999"
        response = client.get(ep)
        assert response.status_code == 404, "This endpoint should return 404"


    def test_status(self, client):
        ep = f"v0.1/valid/beleidskeuzes"
        response = client.get(ep)
        assert response.status_code != 404, "This endpoint should exist"
        assert len(response.get_json()) >= 2, "Should have at least two records"
        ids = []
        for _item in response.get_json():
            assert _item["Status"] == "Vigerend"
            ids.append(_item["ID"])
        assert sorted(ids) == sorted(list(set(ids))), "Double IDs in response that should only show valid objects per lineage"


    def test_valid_filter(self, client_fred):
        ep = f"v0.1/beleidskeuzes?all_filters=Status:Uitgecheckt"
        response = client_fred.get(ep)
        assert response.status_code == 200
        assert len(response.get_json()) > 0, "Should have at least one record"
        for json_obj in response.get_json():
            assert json_obj["Status"] == "Uitgecheckt", "Filter not filtering"


    def test_valid_multiple_filter(self, client_fred):
        ep = f"v0.1/beleidskeuzes?filters=Status:UsedForFiltering,Titel:Title Used For Filtering"
        response = client_fred.get(ep)
        found = False
        for json_obj in response.get_json():
            if json_obj["UUID"] == "82448A0A-989B-11EC-B909-0242AC120002":
                found = True
        assert found, "Did not find the target when filtering"


    def test_invalid_filter(self, client_fred):
        ep = f"v0.1/beleidskeuzes?all_filters=Invalid:not_valid"
        response = client_fred.get(ep)
        assert response.status_code == 400, "This is an invalid request"


    @pytest.mark.parametrize(
        "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
    )
    def test_pagination_limit(self, client, endpoint):
        ep = f"v0.1/{endpoint}?limit=10"
        response = client.get(ep)
        if response.get_json():
            assert len(response.get_json()) <= 10, "Does not limit amount of results"


    @pytest.mark.parametrize(
        "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
    )
    def test_pagination_offset(self, client, endpoint):
        ep = f"v0.1/{endpoint}"
        response = client.get(ep)
        if response.get_json():
            total_count = len(response.get_json())
            response = client.get(f"v0.1/{endpoint}?offset=10")
            assert len(response.get_json()) <= total_count - 10, "Does not offset the results"


    def test_null_begin_geldigheid(self, client_fred):
        ep = f"v0.1/beleidskeuzes"
        test_data = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema,
            user_UUID=client_fred.uuid(),
            excluded_prop="excluded_post",
        )
        test_data["Begin_Geldigheid"] = None
        response = client_fred.post(ep, json=test_data)
        assert response.status_code == 201, f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

        new_uuid = response.get_json()["UUID"]
        ep = f"v0.1/version/beleidskeuzes/{new_uuid}"
        response = client_fred.get(ep)

        assert response.status_code == 200, "Could not get posted object"
        assert response.get_json()["Begin_Geldigheid"] == min_datetime.replace(
            tzinfo=datetime.timezone.utc
        ).isoformat().replace("+00:00", "Z"), "Should be min_datetime"


    def test_null_eind_geldigheid(self, client_fred):
        ep = f"v0.1/beleidskeuzes"
        test_data = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema,
            user_UUID=client_fred.uuid(),
            excluded_prop="excluded_post",
        )
        test_data["Eind_Geldigheid"] = None
        response = client_fred.post(ep, json=test_data)
        assert response.status_code == 201, f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

        new_uuid = response.get_json()["UUID"]
        ep = f"v0.1/version/beleidskeuzes/{new_uuid}"
        response = client_fred.get(ep)

        assert response.status_code == 200, "Could not get posted object"
        assert response.get_json()["Eind_Geldigheid"] == max_datetime.replace(
            tzinfo=datetime.timezone.utc
        ).isoformat().replace("+00:00", "Z"), "Should be min_datetime"


    def test_empty_referencelists(self, client_fred):
        empty_reference_beleidskeuze = copy.deepcopy(reference_rich_beleidsdoel)
        empty_reference_beleidskeuze["Ambities"] = []
        ep = f"v0.1/beleidsdoelen"
        response = client_fred.post(ep, json=empty_reference_beleidskeuze)
        assert response.status_code == 201, f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

        new_uuid = response.get_json()["UUID"]
        new_id = response.get_json()["ID"]
        ep = f"v0.1/version/beleidsdoelen/{new_uuid}"
        response = client_fred.get(ep)
        assert response.status_code == 200, "Could not get posted object"
        assert response.get_json()["Ambities"] == [], "Ambities should be an empty list"

        amb = generate_data(
            ambities.Ambities_Schema,
            user_UUID=client_fred.uuid(),
            excluded_prop="excluded_patch"
        )
        amb["Eind_Geldigheid"] = "9999-12-12T23:59:59Z"
        ep = f"v0.1/ambities"
        response = client_fred.post(ep, json=amb)
        new_uuid = response.get_json()["UUID"]

        ep = f"v0.1/beleidsdoelen/{new_id}"
        response = client_fred.patch(ep, json={"Ambities": [{"UUID": new_uuid}]})
        assert len(response.get_json()["Ambities"]) == 1
        response = client_fred.patch(ep, json={"Ambities": []})

        assert len(response.get_json()["Ambities"]) == 0


    def test_HTML_Validation(self, client_fred):
        ep = f"v0.1/ambities"
        evil_omschrijving = """<h1>Happy</h1><script>console.log('muhaha')</script>"""
        response = client_fred.post(
            ep,
            json={"Titel": "Evil ambitie", "Omschrijving": evil_omschrijving},
        )
        assert response.status_code == 400, f"Status code for POST on {ep} was {response.status_code}, should be 400. Body content: {response.json}"


    def test_reverse_lookup(self, client_fred):
        """
        Test wether reverse lookups work and show the correct inlined objects
        """
        ambitie_data = generate_data(
            ambities.Ambities_Schema,
            user_UUID=client_fred.uuid(),
            excluded_prop="excluded_post",
        )
        ambitie_data["Eind_Geldigheid"] = "9999-12-12T23:59:59Z"
        response = client_fred.post(
            "v0.1/ambities",
            json=ambitie_data,
        )
        assert response.status_code == 201, f"Status code for POST was {response.status_code}, should be 201. Body content: {response.json}"
        assert response.get_json()["Ref_Beleidskeuzes"] == [], f"Reverse lookup not empty on post. Body content: {response.json}"
        ambitie_id = response.get_json()["ID"]
        ambitie_uuid = response.get_json()["UUID"]

        # Create a new Beleidskeuze
        beleidskeuze_data = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema,
            user_UUID=client_fred.uuid(),
            excluded_prop="excluded_post",
        )
        # Set ambities
        beleidskeuze_data["Ambities"] = [
            {"UUID": ambitie_uuid, "Koppeling_Omschrijving": "Test description"}
        ]
        # Set status
        beleidskeuze_data["Status"] = "Vigerend"
        beleidskeuze_data["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=beleidskeuze_data)
        assert response.status_code == 201, f"Status code for POST was {response.status_code}, should be 201. Body content: {response.json}"
        assert response.get_json()["Ambities"][0]["Object"]["UUID"] == ambitie_uuid, f"Nested objects are not on object. Body content: {response.json}"

        beleidskeuze_id = response.get_json()["ID"]
        beleidskeuze_uuid = response.get_json()["UUID"]
        # Get the ambitie
        response = client_fred.get(f"v0.1/ambities/{ambitie_id}")
        assert response.status_code == 200, f"Status code for GET was {response.status_code}, should be 200. Body content: {response.json}"
        assert len(response.get_json()[0]["Ref_Beleidskeuzes"]) == 1, f"Wrong amount of objects in reverse lookup field. Lookup field: {response.get_json()[0]['Ref_Beleidskeuzes']}"
        assert response.get_json()[0]["Ref_Beleidskeuzes"][0]["UUID"] == beleidskeuze_uuid, f"Nested objects are not on object. Body content: {response.json}"

        # Add a new version to the lineage
        response = client_fred.patch(f"v0.1/beleidskeuzes/{beleidskeuze_id}", json={"Titel": "New Title"})
        assert response.status_code == 200, f"Status code for POST was {response.status_code}, should be 200. Body content: {response.json}"
        assert response.get_json()["Ambities"][0]["Object"]["UUID"] == ambitie_uuid, f"Nested objects are not on object. Body content: {response.json}"
        beleidskeuze_latest_id = response.get_json()["ID"]
        beleidskeuze_latest_uuid = response.get_json()["UUID"]

        # Get the ambitie
        response = client_fred.get(f"v0.1/ambities/{ambitie_id}")
        assert response.status_code == 200, f"Status code for GET was {response.status_code}, should be 200. Body content: {response.json}"
        assert len(response.get_json()[0]["Ref_Beleidskeuzes"]) == 1, f"Too many objects in reverse lookup field. Lookup field: {response.get_json()[0]['Ref_Beleidskeuzes']}"
        assert response.get_json()[0]["Ref_Beleidskeuzes"][0]["UUID"] == beleidskeuze_latest_uuid, f"Nested objects are on object. Body content: {response.json}"


    def test_non_copy_field(self, client_fred):
        # create beleidskeuze lineage
        test_data = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema,
            user_UUID=client_fred.uuid(),
            excluded_prop="excluded_post",
        )
        ep = f"v0.1/beleidskeuzes"
        response = client_fred.post(ep, json=test_data)
        assert response.status_code == 201, f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

        first_uuid = response.get_json()["UUID"]
        ep = f"v0.1/beleidskeuzes/{response.get_json()['ID']}"
        # Patch a new aanpassing_op field
        response = client_fred.patch(ep, json={"Titel": "Patched", "Aanpassing_Op": first_uuid})
        assert response.status_code == 200, f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
        assert response.get_json()["Aanpassing_Op"] == first_uuid, "Aanpassing_Op not saved!"

        # Patch a different field, aanpassing_op should be null
        response = client_fred.patch(ep, json={"Titel": "Patched twice"})
        assert response.status_code == 200, f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
        assert response.get_json()["Aanpassing_Op"] == None, "Aanpassing_Op was copied!"


    def test_all_filters(self, client_fred):
        ep = f"v0.1/beleidskeuzes"
        response = client_fred.get(ep + "?all_filters=Status:Vigerend,Titel:Second")
        assert response.status_code == 200, f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
        for obj in response.get_json():
            assert obj["Titel"] == "Second", 'Titel should be "Second"'
            assert obj["Status"] == "Vigerend", 'Status should be "Vigerend"'


    def test_multiple_filters(self, client_fred):
        ep = f"v0.1/beleidskeuzes"
        response = client_fred.get(ep + "?any_filters=Titel:Test4325123$%,Afweging:Test4325123$%")
        assert response.status_code == 200, f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
        assert len(response.get_json()) >= 3, "Expecting at least three objects with these criteria"


    def test_clear_patch_fields_beleidskeuzes(self, db, client_fred):
        given_uuid = "94A45F78-98A9-11EC-B909-0242AC120002"
        keuze = db.session.query(Beleidskeuzes).filter(Beleidskeuzes.UUID == given_uuid).first()
        assert keuze, f"Expect beleidskeuze with UUID {given_uuid} to exist"

        modify_data = {"Titel": "Nieuwe Titel", "Aanpassing_Op": given_uuid}
        ep = f"v0.1/beleidskeuzes/{keuze.ID}"
        response = client_fred.patch(ep, json=modify_data)
        assert response.status_code == 200, f"Status code for PATCH on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
        assert response.get_json()["Aanpassing_Op"] == given_uuid

        modify_data = {"Titel": "Nieuwere Titel"}
        response = client_fred.patch(ep, json=modify_data)
        assert response.get_json()["Aanpassing_Op"] == None


    def test_clear_patch_fields_maatregelen(self, db, client_fred):
        given_uuid = "38909E6A-98AC-11EC-B909-0242AC120002"
        maatregel = db.session.query(Maatregelen).filter(Maatregelen.UUID == given_uuid).first()
        assert maatregel, f"Expect maatregel with UUID {given_uuid} to exist"

        modify_data = {"Titel": "Nieuwe Titel", "Aanpassing_Op": given_uuid}
        patch_ep = f"v0.1/maatregelen/{maatregel.ID}"
        response = client_fred.patch(patch_ep, json=modify_data)

        assert response.status_code == 200, f"Status code for PATCH on {patch_ep} was {response.status_code}, should be 200. Body content: {response.json}"
        assert response.get_json()["Aanpassing_Op"] == given_uuid

        modify_data = {"Titel": "Nieuwere Titel"}
        response = client_fred.patch(patch_ep, json=modify_data)
        assert response.get_json()["Aanpassing_Op"] == None


    def test_graph_ep(self, client, client_fred):
        ep = f"v0.1/graph"
        response = client_fred.get(ep)
        assert response.status_code == 200, "Graph endpoint not working"

        response = client.get(ep)
        assert response.status_code == 200, "Graph endpoint is unavailable without auth"


    def test_null_date(self, db, client_fred):
        given_uuid = "B5f7C134-98AD-11EC-B909-0242AC120002"
        prestatie = db.session.query(Beleidsprestaties).filter(Beleidsprestaties.UUID == given_uuid).first()
        assert prestatie, f"Expect prestatie with UUID {given_uuid} to exist"

        ep = f"v0.1/beleidsprestaties/{prestatie.ID}"
        response = client_fred.patch(ep, json={"Eind_Geldigheid": None})
        assert response.status_code == 200, "patch failed"

        response = client_fred.get(ep)
        assert response.get_json()[0]["Eind_Geldigheid"] == "9999-12-31T23:59:59Z"


    def test_gebiedsprogrammas_afbeelding(self, db, client_fred):
        # Create a new Gebiedsprogramma
        data = generate_data(
            gebiedsprogrammas.Gebiedsprogrammas_Schema,
            user_UUID=client_fred.uuid(),
            excluded_prop="excluded_post",
        )

        with open("./Tests/TestUtils/image-1.png", "rb") as image:
            afbeelding_1_binary = image.read()
            afbeelding_1_b64_bytes = base64.b64encode(afbeelding_1_binary)
            afbeeling_1_b64_string = afbeelding_1_b64_bytes.decode("utf-8")

        with open("./Tests/TestUtils/image-2.png", "rb") as image:
            afbeelding_2_binary = image.read()
            afbeelding_2_b64_bytes = base64.b64encode(afbeelding_2_binary)
            afbeeling_2_b64_string = afbeelding_2_b64_bytes.decode("utf-8")

        data["Afbeelding"] = afbeeling_1_b64_string
        data["Status"] = "Vigerend"
        data["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"

        response = client_fred.post("v0.1/gebiedsprogrammas", json=data)
        assert response.status_code == 201, f"Status code for POST was {response.status_code}, should be 201. Body content: {response.json}"
        assert response.get_json()["Afbeelding"] == afbeeling_1_b64_string

        gebiedsprogramma_id = response.get_json()["ID"]

        # Add a new version to the lineage
        # Do not change the Afbeelding
        response = client_fred.patch(f"v0.1/gebiedsprogrammas/{gebiedsprogramma_id}", json={
            "Titel": "New Title 1",
        })
        assert response.status_code == 200, f"Status code for POST was {response.status_code}, should be 200. Body content: {response.json}"
        assert response.get_json()["Afbeelding"] == afbeeling_1_b64_string

        # Add a new version to the lineage
        # Change the Afbeelding
        response = client_fred.patch(f"v0.1/gebiedsprogrammas/{gebiedsprogramma_id}", json={
            "Titel": "New Title 2",
            "Afbeelding": afbeeling_2_b64_string,
        })
        assert response.status_code == 200, f"Status code for POST was {response.status_code}, should be 200. Body content: {response.json}"
        assert response.get_json()["Afbeelding"] == afbeeling_2_b64_string

        # # Get the changed afbeelding
        response = client_fred.get(f"v0.1/gebiedsprogrammas/{gebiedsprogramma_id}")
        assert response.status_code == 200, f"Status code for GET was {response.status_code}, should be 200. Body content: {response.json}"
        assert response.get_json()[0]["Afbeelding"] == afbeeling_2_b64_string


    #
    # @todo: From here we should try te remove generate_data
    #           if it does not explicitly used for the main purpose of the test
    #           for example it is not needed for fetch requests
    #           but it is needed to check if creating a new model works 
    #


    def test_graph_normal(self, client_fred):
        # Create Ambitie
        test_amb = generate_data(ambities.Ambities_Schema, excluded_prop="excluded_post")
        test_amb["Eind_Geldigheid"] = "2992-11-23T10:00:00"
        amb_resp = client_fred.post("v0.1/ambities", json=test_amb)
        amb_UUID = amb_resp.get_json()["UUID"]

        # Create Belang
        test_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
        test_belang["Eind_Geldigheid"] = "2992-11-23T10:00:00"
        belang_resp = client_fred.post("v0.1/belangen", json=test_belang)
        belang_UUID = belang_resp.get_json()["UUID"]

        # Create Belang that is not valid anymore
        test_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
        test_belang["Eind_Geldigheid"] = "1992-11-23T10:00:00"
        belang_resp = client_fred.post("v0.1/belangen", json=test_belang)
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
        response = client_fred.post("v0.1/beleidskeuzes", json=test_bk)
        bk_uuid = response.get_json()["UUID"]

        # Do Check
        response = client_fred.get("v0.1/graph")
        graph_links = response.get_json()["links"]
        graph_nodes = response.get_json()["nodes"]
        found_links = []

        for link in graph_links:
            if link["source"] == bk_uuid:
                found_links.append(link["target"])
        assert not invalid_belang_UUID in found_links, "Invalid belang retrieved"
        assert len(found_links) == 2, "Not all links retrieved"
        assert belang_UUID in found_links, "Belang not retrieved"
        assert amb_UUID in found_links, "Ambitie not retrieved"
        assert set([amb_UUID, belang_UUID]) == set(found_links), "Unexpected result for links"


    def test_module_UUID(self, client_fred):
        # Create beleidskeuze (add objects)
        test_bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        response = client_fred.post("v0.1/beleidskeuzes", json=test_bk)
        new_uuid = response.get_json()["UUID"]
        new_id = response.get_json()["ID"]

        # Create Module
        test_module = generate_data(
            beleidsmodule.Beleidsmodule_Schema, excluded_prop="excluded_post"
        )
        test_module["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        test_module["Beleidskeuzes"] = [{"UUID": new_uuid, "Koppeling_Omschrijving": ""}]
        response = client_fred.post("v0.1/beleidsmodules", json=test_module)
        assert response.status_code == 201
        module_uuid = response.get_json()["UUID"]

        # Check reverse
        response = client_fred.get(f"v0.1/beleidskeuzes/{new_id}")
        assert response.status_code == 200
        assert response.get_json()[0]["Ref_Beleidsmodules"][0]["UUID"] == module_uuid

        # Add new version to bk
        response = client_fred.patch(f"v0.1/beleidskeuzes/{new_id}", json={"Titel": "Nieuwe Titel"})
        # Check reverse again
        response = client_fred.get(f"v0.1/beleidskeuzes/{new_id}")
        assert response.status_code == 200
        assert not (response.get_json()[0]["Ref_Beleidsmodules"]), "Should not be in module"


    def test_maatregelen_link(self, client_fred):
        # Create Maatregel
        test_ma = generate_data(
            maatregelen.Maatregelen_Schema, excluded_prop="excluded_post"
        )
        test_ma["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        test_ma["Status"] = "Vigerend"
        response = client_fred.post("v0.1/maatregelen", json=test_ma)
        ma_uuid = response.get_json()["UUID"]

        # Create beleidskeuze (add objects)
        test_bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        test_bk["Maatregelen"] = [{"UUID": ma_uuid, "Koppeling_Omschrijving": "Test"}]
        response = client_fred.post("v0.1/beleidskeuzes", json=test_bk)
        bk_id = response.get_json()["ID"]

        # Check beleidskeuze
        response = client_fred.get(f"v0.1/beleidskeuzes/{bk_id}", json=test_bk)
        assert response.get_json()[0]["Maatregelen"], "references where empty"
        assert (
            response.get_json()[0]["Maatregelen"][0]["Object"]["UUID"] == ma_uuid
        ), "Maatregel not linked"


    def test_valid(self, client, client_fred):
        # Create Belang
        old_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
        old_belang["Eind_Geldigheid"] = "1992-11-23T10:00:00"
        new_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
        new_belang["Eind_Geldigheid"] = "2992-11-23T10:00:00"

        response = client_fred.post("v0.1/belangen", json=old_belang)
        old_belang_uuid = response.get_json()["UUID"]
        response = client_fred.post("v0.1/belangen", json=new_belang)
        new_belang_uuid = response.get_json()["UUID"]

        response = client.get("v0.1/valid/belangen")
        found_new = False
        for belang in response.get_json():
            assert belang["UUID"] != old_belang_uuid
            if belang["UUID"] == new_belang_uuid:
                found_new = True
        assert found_new


    def test_protect_invalid(self, client, client_fred):
        response = client.get("v0.1/belangen")
        assert response.status_code == 401, f"body: {response.get_json()}"
        response = client_fred.get("v0.1/belangen")
        assert response.status_code == 200
        response = client.get("v0.1/valid/belangen")
        assert response.status_code == 200


    def test_filter(self, client_fred):
        response = client_fred.get(f"v0.1/beleidsmodules?any_filters=Created_By:{client_fred.uuid()}")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 3, "Expecting at least 3 results from Fred"


    def test_non_valid_reference(self, client_fred):
        # Create Maatregel
        test_ma = generate_data(
            maatregelen.Maatregelen_Schema, excluded_prop="excluded_post"
        )
        test_ma["Status"] = "Ontwerp GS Concept"
        response = client_fred.post("v0.1/maatregelen", json=test_ma)
        ma_uuid = response.get_json()["UUID"]

        # Create beleidskeuze
        test_bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        test_bk["Status"] = "Ontwerp GS Concept"
        test_bk["Maatregelen"] = [{"UUID": ma_uuid, "Koppeling_Omschrijving": "Test"}]
        response = client_fred.post("v0.1/beleidskeuzes", json=test_bk)
        bk_id = response.get_json()["ID"]

        # Check beleidskeuze
        response = client_fred.get(f"v0.1/beleidskeuzes/{bk_id}", json=test_bk)
        assert len(response.get_json()[0]["Maatregelen"]) == 1, "references should not be empty"


    def test_graph_relation(self, client, client_fred):
        # Create BK1 & BK2 (valid)
        bk_1 = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk_2 = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )

        bk_1["Status"] = "Vigerend"
        bk_1["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk_1)
        assert response.status_code == 201, f"{response.get_json()}"
        bk_1_UUID = response.get_json()["UUID"]
        bk_2["Status"] = "Vigerend"
        bk_2["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        
        response = client_fred.post("v0.1/beleidskeuzes", json=bk_2)
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
        response = client_fred.post("v0.1/beleidsrelaties", json=br)
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


    def test_reverse_valid_check(self, client, client_fred):
        amb = generate_data(ambities.Ambities_Schema, excluded_prop="excluded_post")
        response = client_fred.post("v0.1/ambities", json=amb)
        assert response.status_code == 201
        assert response.get_json()["Ref_Beleidskeuzes"] == [], "should be empty because nothing refers to this"

        amb_uuid = response.get_json()["UUID"]
        bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk["Status"] = "Ontwerp GS Concept"
        bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        bk["Ambities"] = [{"UUID": amb_uuid, "Koppeling_Omschrijving": ""}]
        response = client_fred.post("v0.1/beleidskeuzes", json=bk)

        assert response.status_code == 201, f"Failed to create beleidskeuze: {response.get_json()}"
        response = client.get(f"v0.1/version/ambities/{amb_uuid}")
        assert response.get_json()["Ref_Beleidskeuzes"] == [], "should be empty because beleidskeuze is not valid"
        assert response.status_code == 200, f"Failed to get ambitie: {response.get_json()}"


    def test_future_links(self, client, client_fred):
        amb = generate_data(ambities.Ambities_Schema, excluded_prop="excluded_post")
        future = datetime.datetime.now() + datetime.timedelta(days=2)
        amb["Begin_Geldigheid"] = future.strftime("%Y-%m-%dT%H:%M:%SZ")
        amb["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/ambities", json=amb)
        assert response.status_code == 201
        assert response.get_json()["Ref_Beleidskeuzes"] == [], "should be empty because nothing refers to this"
        
        amb_uuid = response.get_json()["UUID"]
        response = client.get("v0.1/valid/ambities")
        assert amb_uuid not in map(lambda ob: ob.get("UUID"), response.get_json())

        bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk["Status"] = "Vigerend"
        bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        bk["Ambities"] = [{"UUID": amb_uuid}]

        response = client_fred.post("v0.1/beleidskeuzes", json=bk)
        assert response.status_code == 201
        assert response.get_json()["Ambities"] == [], "Ambitie is not yet valid"

        bk_uuid = response.get_json()["UUID"]
        response = client.get(f"v0.1/version/beleidskeuzes/{bk_uuid}")
        assert response.get_json()["Ambities"] == [], "Ambitie is not yet valid"


    def test_latest_version(self, client, client_fred):
        bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk["Status"] = "Ontwerp GS Concept"
        bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk)
        assert response.status_code == 201
        bk_ID = response.get_json()["ID"]
        bk_UUID = response.get_json()["UUID"]

        bk["Status"] = "Ontwerp PS"
        response = client_fred.patch(f"v0.1/beleidskeuzes/{bk_ID}", json=bk)
        assert response.status_code == 200
        new_bk_UUID = response.get_json()["UUID"]

        response = client.get(f"v0.1/version/beleidskeuzes/{bk_UUID}")
        assert response.status_code == 200
        assert response.get_json()["Latest_Version"] == new_bk_UUID
        assert response.get_json()["Latest_Status"] == "Ontwerp PS"


    def test_effective_version(self, client, client_fred):
        bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk["Status"] = "Vigerend"
        bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk)
        assert response.status_code == 201
        bk_ID = response.get_json()["ID"]
        bk_UUID = response.get_json()["UUID"]

        bk["Status"] = "Ontwerp PS"
        response = client_fred.patch(f"v0.1/beleidskeuzes/{bk_ID}", json=bk)
        assert response.status_code == 200
        new_bk_UUID = response.get_json()["UUID"]

        response = client.get(f"v0.1/version/beleidskeuzes/{new_bk_UUID}")
        assert response.status_code == 200
        assert response.get_json()["Effective_Version"] == bk_UUID


    def test_ID_relations_valid(self, client, client_fred):
        # Create two beleidskeuzes
        bk_a = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk_a["Status"] = "Vigerend"
        bk_a["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response_a = client_fred.post("v0.1/beleidskeuzes", json=bk_a)
        a_uuid = response_a.get_json()['UUID']    
        a_id = response_a.get_json()['ID']    

        bk_b = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk_b["Status"] = "Vigerend"
        bk_b["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response_b = client_fred.post("v0.1/beleidskeuzes", json=bk_b)
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
        response_br = client_fred.post("v0.1/beleidsrelaties", json=br)
        
        assert response_br.status_code == 201
        br_uuid = response_br.get_json()['UUID']
        br_id = response_br.get_json()['ID']
        response_get_br = client.get(f"v0.1/beleidsrelaties/{br_id}")
        assert response_get_br.status_code == 200
        assert response_br.get_json()['Van_Beleidskeuze']['UUID'] == a_uuid
        assert response_br.get_json()['Naar_Beleidskeuze']['UUID'] == b_uuid

        # Update beleidskeuze b
        response_patch_b = client_fred.patch(f"v0.1/beleidskeuzes/{b_id}", json={**bk_b, 'Titel':'SWEN'})
        b_patch_uuid = response_patch_b.get_json()['UUID']    

        response_get_br = client.get(f"v0.1/beleidsrelaties/{br_id}")
        assert response_get_br.status_code == 200
        # Expect the new beleidskeuze to show    
        assert response_get_br.get_json()[0]['Van_Beleidskeuze']['UUID'] == a_uuid
        assert response_get_br.get_json()[0]['Naar_Beleidskeuze']['UUID'] == b_patch_uuid

        # Also check the single version
        response_get_br_ver = client.get(f"v0.1/version/beleidsrelaties/{br_uuid}")
        assert response_get_br_ver.status_code == 200
        assert response_get_br_ver.get_json()['Van_Beleidskeuze']['UUID'] == a_uuid
        assert response_get_br_ver.get_json()['Naar_Beleidskeuze']['UUID'] == b_patch_uuid
        
        # Check BR in valid view
        response_get_br_valid = client.get(f"v0.1/valid/beleidsrelaties")
        assert br_uuid in (map(lambda br: br['UUID'], response_get_br_valid.get_json()))


    def test_ID_relations_full(self, client, client_fred):
        # Create two beleidskeuzes
        bk_a = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk_a["Status"] = "Vigerend"
        bk_a["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response_a = client_fred.post("v0.1/beleidskeuzes", json=bk_a)
        a_uuid = response_a.get_json()['UUID']    
        a_id = response_a.get_json()['ID']    

        bk_b = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk_b["Status"] = "Vigerend"
        bk_b["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response_b = client_fred.post("v0.1/beleidskeuzes", json=bk_b)
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
        response_br = client_fred.post("v0.1/beleidsrelaties", json=br)
        assert response_br.status_code == 201

        br_uuid = response_br.get_json()['UUID']
        br_id = response_br.get_json()['ID']
        response_get_br = client.get(f"v0.1/beleidsrelaties/{br_id}")
        assert response_get_br.status_code == 200
        assert response_br.get_json()['Van_Beleidskeuze']['UUID'] == a_uuid
        assert response_br.get_json()['Naar_Beleidskeuze']['UUID'] == b_uuid

        # Update beleidskeuze b
        data = {**bk_b, 'Titel':'SWEN', 'Status':'Ontwerp GS'}
        response_patch_b = client_fred.patch(f"v0.1/beleidskeuzes/{b_id}", json=data)
        b_patch_uuid = response_patch_b.get_json()['UUID']    

        all_response = client_fred.get(f"v0.1/beleidsrelaties")
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


    def test_edits_200(self, client):
        response = client.get('v0.1/edits')
        assert response.status_code == 200


    def test_edits_latest(self, client, client_fred):
        bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk)
        bk_uuid = response.get_json()['UUID']

        response = client.get('v0.1/edits')
        assert response.status_code == 200
        assert response.get_json()[0]['UUID'] == bk_uuid


    def test_edits_vigerend(self, client, client_fred):
        bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk)
        bk_uuid = response.get_json()['UUID']
        bk_id = response.get_json()['ID']

        response = client_fred.patch(f"v0.1/beleidskeuzes/{bk_id}", json={'Status':'Vigerend'})
        assert response.status_code == 200

        response = client.get('v0.1/edits')
        assert response.status_code == 200
        for row in response.get_json():
            assert row['ID'] != bk_id 


    def test_empty_edit(self, client, client_fred):
        bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk["Status"] = "Vigerend"
        bk["Eind_Geldigheid"] = "9999-12-31T23:59:59"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk)
        assert response.status_code == 201
        bk_ID = response.get_json()["ID"]
        bk_UUID = response.get_json()["UUID"]

        # Patch without changes
        response = client_fred.patch(f"v0.1/beleidskeuzes/{bk_ID}", json=bk)
        assert response.get_json()['UUID'] == bk_UUID


    def test_module_concept(self, client, client_fred):
        """A module should show non-effective objects
        """
        # Create non effective beleidskeuze
        test_bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        test_bk['Status'] = 'Ontwerp GS'
        test_bk['Begin_Geldigheid'] = "1900-12-31T23:59:59Z"
        test_bk['Eind_Geldigheid'] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=test_bk)
        bk_uuid = response.get_json()["UUID"]
        bk_id = response.get_json()["ID"]

        # Create Module
        test_module = generate_data(
            beleidsmodule.Beleidsmodule_Schema, excluded_prop="excluded_post"
        )
        test_module["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        test_module["Beleidskeuzes"] = [{"UUID": bk_uuid, "Koppeling_Omschrijving": ""}]
        response = client_fred.post("v0.1/beleidsmodules", json=test_module)
        assert response.status_code == 201
        module_uuid = response.get_json()["UUID"]
        module_id = response.get_json()["ID"]

        # Check module
        response = client.get(f"v0.1/beleidsmodules/{module_id}")
        assert response.status_code == 200
        assert len(response.get_json()[0]["Beleidskeuzes"]) == 1
        assert response.get_json()[0]["Beleidskeuzes"][0]['Object']["UUID"] == bk_uuid


    def test_module_multiple_concept(self, client, client_fred):
        """A module should show non-effective objects
        """
        # Create non effective beleidskeuze
        test_bk = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        test_bk['Status'] = 'Ontwerp GS'
        test_bk['Begin_Geldigheid'] = "1900-12-31T23:59:59Z"
        test_bk['Eind_Geldigheid'] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=test_bk)
        bk_uuid = response.get_json()["UUID"]
        bk_id = response.get_json()["ID"]

        # Create Module
        test_module = generate_data(
            beleidsmodule.Beleidsmodule_Schema, excluded_prop="excluded_post"
        )
        test_module["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        test_module["Beleidskeuzes"] = [{"UUID": bk_uuid, "Koppeling_Omschrijving": ""}]

        response = client_fred.post("v0.1/beleidsmodules", json=test_module)
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
        response = client_fred.post("v0.1/maatregelen", json=test_ma)
        ma_uuid = response.get_json()["UUID"]
        ma_id = response.get_json()["ID"]

        data = {'Maatregelen': [{"UUID": ma_uuid, "Koppeling_Omschrijving": ""}]}
        response = client_fred.patch(f"v0.1/beleidsmodules/{module_id}", json=data)
        assert response.status_code == 200

        # Check module
        response = client.get(f"v0.1/beleidsmodules/{module_id}")
        assert response.status_code == 200
        assert len(response.get_json()[0]["Beleidskeuzes"]) == 1
        assert len(response.get_json()[0]["Maatregelen"]) == 1
        assert response.get_json()[0]["Beleidskeuzes"][0]['Object']["UUID"] == bk_uuid
        assert response.get_json()[0]["Maatregelen"][0]['Object']["UUID"] == ma_uuid


    def test_latest_middle(self, client, client_fred):
        bk1 = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk1["Status"] = "Ontwerp GS Concept"
        bk1["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk1)
        assert response.status_code == 201
        bk_ID = response.get_json()["ID"]
        bk1_UUID = response.get_json()["UUID"]
        bk_2 = {**bk1, 'Status':['Ontwerp GS']}

        response = client_fred.patch(f"v0.1/beleidskeuzes/{bk_ID}", json={'Status':'Ontwerp GS'})
        assert response.status_code == 200, response.get_json()
        bk2_UUID = response.get_json()["UUID"]

        # Check if latest version matches
        response = client.get(f"v0.1/version/beleidskeuzes/{bk1_UUID}")
        assert response.status_code == 200
        assert response.get_json()["Latest_Version"] == bk2_UUID
        assert response.get_json()["Latest_Status"] == "Ontwerp GS"

        data = {'Status':'Vigerend', 'Begin_Geldigheid':"2010-12-31T23:59:59Z", 'Eind_Geldigheid':"2011-12-31T23:59:59Z" }
        response = client_fred.patch(f"v0.1/beleidskeuzes/{bk_ID}", json=data)
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


    def test_self_effective_version(self, client, client_fred):
        bk1 = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk1["Status"] = "Vigerend"
        bk1["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk1)
        assert response.status_code == 201
        bk1_UUID = response.get_json()["UUID"]
        bk_ID = response.get_json()["ID"]

        # Check if latest version matches
        response = client.get(f"v0.1/version/beleidskeuzes/{bk1_UUID}")
        assert response.status_code == 200
        assert response.get_json()["Effective_Version"] == bk1_UUID
        
        # Make new version
        response = client_fred.patch(f"v0.1/beleidskeuzes/{bk_ID}", json={'Status':'Ontwerp GS'})
        assert response.status_code == 200

        # Check if latest version matches
        response = client.get(f"v0.1/version/beleidskeuzes/{bk1_UUID}")
        assert response.status_code == 200
        assert response.get_json()["Effective_Version"] == bk1_UUID


    def test_effective_in_edits(self, client, client_fred):
        bk1 = generate_data(
            beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
        )
        bk1["Status"] = "Vigerend"
        bk1["Eind_Geldigheid"] = "9999-12-31T23:59:59Z"
        response = client_fred.post("v0.1/beleidskeuzes", json=bk1)
        assert response.status_code == 201
        bk1_UUID = response.get_json()["UUID"]
        bk_ID = response.get_json()["ID"]
        
        # Make new version
        response = client_fred.patch(f"v0.1/beleidskeuzes/{bk_ID}", json={'Status':'Ontwerp GS'})
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


    @pytest.mark.parametrize(
        "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
    )
    def test_endpoints_not_authenticated(self, client, endpoint):
        if endpoint.Meta.slug in ["beleidsrelaties", "beleidsmodules"]:
            return
        list_ep = f"v0.1/{endpoint.Meta.slug}"
        response = client.get(list_ep)
        assert response.status_code == 401, f"Status code for GET on {list_ep} was {response.status_code}, should be 401. Response body: {response.get_json()}"


    @pytest.mark.parametrize(
        "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
    )
    def test_endpoints_create_and_patch_most_endpoints(self, client_fred, endpoint):
        if endpoint.Meta.slug in ["beleidsrelaties", "beleidsmodules"]:
            return

        list_ep = f"v0.1/{endpoint.Meta.slug}"
        response = client_fred.get(list_ep)
        assert response.status_code == 200, f"Status code for GET on {list_ep} was {response.status_code}, should be 200. Response body: {response.get_json()}"
        found_count = len(response.get_json())
        assert found_count != 0, f"Expecting at least one record for each model but found 0 for {endpoint.Meta.slug}"

        t_uuid = response.json[0]["UUID"]
        version_ep = f"v0.1/version/{endpoint.Meta.slug}/{t_uuid}"
        response = client_fred.get(version_ep)
        assert response.status_code == 200, f"Status code for GET on {version_ep} was {response.status_code}, should be 200."

        valid_ep = f"v0.1/valid/{endpoint.Meta.slug}"
        response = client_fred.get(valid_ep)
        assert response.status_code == 200, f"Status code for GET on {valid_ep} was {response.status_code}, should be 200."

        if not endpoint.Meta.read_only:
            # create a new record
            test_data = generate_data(
                endpoint, user_UUID=client_fred.uuid(), excluded_prop="excluded_post"
            )

            response = client_fred.post(list_ep, json=test_data)
            assert response.status_code == 201, f"Status code for POST on {list_ep} was {response.status_code}, should be 201. Body content: {response.json}"
            new_id = response.get_json()["ID"]

            # validate that we have a new record
            response = client_fred.get(list_ep)
            assert found_count + 1 == len(response.get_json()), "No new object after POST"

            new_date = "1994-11-23T10:00:00Z"
            response = client_fred.patch(list_ep + "/" + str(new_id), json={"Begin_Geldigheid": new_date})
            assert response.status_code == 200, f"Status code for PATCH on {list_ep} was {response.status_code}, should be 200. Body contents: {response.json}"

            response = client_fred.get(list_ep + "/" + str(new_id))
            assert response.json[0]["Begin_Geldigheid"] == new_date, "Patch did not change object."
            response = client_fred.get(list_ep)
