# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import pytest
from pprint import pprint

from Api.settings import null_uuid
from Api.datamodel import endpoints
from Tests.TestUtils.schema_data import generate_data, reference_rich_beleidskeuze


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
