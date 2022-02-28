# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import pytest
from pprint import pprint
import datetime
import copy

from Api.settings import null_uuid, min_datetime, max_datetime
from Api.datamodel import endpoints
from Tests.TestUtils.schema_data import generate_data, reference_rich_beleidskeuze
from Api.Models import (
    beleidskeuzes,
    ambities,
    beleidsrelaties,
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
        ep = f"v0.1/beleidskeuzes"
        response = client_fred.post(ep, json=reference_rich_beleidskeuze)
        assert response.status_code == 201, f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

        new_id = response.get_json()["ID"]
        ep = f"v0.1/beleidskeuzes/{new_id}"
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
        empty_reference_beleidskeuze = copy.deepcopy(reference_rich_beleidskeuze)
        empty_reference_beleidskeuze["Ambities"] = []
        ep = f"v0.1/beleidskeuzes"
        response = client_fred.post(ep, json=empty_reference_beleidskeuze)
        assert response.status_code == 201, f"Status code for POST on {ep} was {response.status_code}, should be 201. Body content: {response.json}"

        new_uuid = response.get_json()["UUID"]
        new_id = response.get_json()["ID"]
        ep = f"v0.1/version/beleidskeuzes/{new_uuid}"
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

        ep = f"v0.1/beleidskeuzes/{new_id}"
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


    # def test_graph_normal(self, client_fred):
    #     # Create Ambitie
    #     test_amb = generate_data(ambities.Ambities_Schema, excluded_prop="excluded_post")
    #     test_amb["Eind_Geldigheid"] = "2992-11-23T10:00:00"
    #     amb_resp = client.post(
    #         "v0.1/ambities", json=test_amb, headers={"Authorization": f"Bearer {auth[1]}"}
    #     )
    #     amb_UUID = amb_resp.get_json()["UUID"]

    #     # Create Belang
    #     test_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
    #     test_belang["Eind_Geldigheid"] = "2992-11-23T10:00:00"
    #     belang_resp = client.post(
    #         "v0.1/belangen",
    #         json=test_belang,
    #         headers={"Authorization": f"Bearer {auth[1]}"},
    #     )
    #     belang_UUID = belang_resp.get_json()["UUID"]

    #     # Create Belang that is not valid anymore
    #     test_belang = generate_data(belangen.Belangen_Schema, excluded_prop="excluded_post")
    #     belang_resp = client.post(
    #         "v0.1/belangen",
    #         json=test_belang,
    #         headers={"Authorization": f"Bearer {auth[1]}"},
    #     )
    #     invalid_belang_UUID = belang_resp.get_json()["UUID"]

    #     # Create beleidskeuze (add objects)
    #     test_bk = generate_data(
    #         beleidskeuzes.Beleidskeuzes_Schema, excluded_prop="excluded_post"
    #     )
    #     test_bk["Eind_Geldigheid"] = "2992-11-23T10:00:00"
    #     test_bk["Ambities"] = [{"UUID": amb_UUID, "Koppeling_Omschrijving": ""}]
    #     test_bk["Belangen"] = [
    #         {"UUID": belang_UUID, "Koppeling_Omschrijving": ""},
    #         {"UUID": invalid_belang_UUID, "Koppeling_Omschrijving": ""},
    #     ]
    #     test_bk["Status"] = "Vigerend"
    #     response = client.post(
    #         "v0.1/beleidskeuzes",
    #         json=test_bk,
    #         headers={"Authorization": f"Bearer {auth[1]}"},
    #     )
    #     bk_uuid = response.get_json()["UUID"]

    #     # Do Check
    #     response = client.get("v0.1/graph", headers={"Authorization": f"Bearer {auth[1]}"})
    #     graph_links = response.get_json()["links"]
    #     graph_nodes = response.get_json()["nodes"]
    #     found_links = []

    #     for link in graph_links:
    #         if link["source"] == bk_uuid:
    #             found_links.append(link["target"])
    #     assert len(found_links) == 2, "Not all links retrieved"
    #     assert belang_UUID in found_links, "Belang not retrieved"
    #     assert not invalid_belang_UUID in found_links, "Invalid belang retrieved"
    #     assert amb_UUID in found_links, "Ambitie not retrieved"
    #     assert set([amb_UUID, belang_UUID]) == set(
    #         found_links
    #     ), "Unexpected result for links"
































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
