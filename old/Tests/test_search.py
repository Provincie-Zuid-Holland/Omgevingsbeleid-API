# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import pytest

from Api.settings import null_uuid


@pytest.mark.usefixtures("fixture_data", "wait_for_fulltext_index")
class TestSearch:
    """
    Note: We are always expecting "at least" counts because
    the Faker package might actually create additional matching data
    """

    def test_geo_endpoints(self, client):
        specials = [f"v0.1/search/geo?query={null_uuid},{null_uuid}"]
        for special in specials:
            response = client.get(special)
            assert response.status_code == 200

    def test_fieldset(self, client):
        res = client.get("v0.1/search?query=water")
        assert res.status_code == 200

        data = res.get_json()
        assert "total" in data, "Expecting a total property"
        assert "results" in data, "Expecting a results property"
        assert len(data["results"]) >= 1, "Expecting at least one result"
        assert list(data["results"][0].keys()) == [
            "Omschrijving",
            "RANK",
            "Titel",
            "Type",
            "UUID",
        ]

    def test_keywords(self, client):
        res = client.get("v0.1/search?query=en")
        assert res.status_code == 200
        assert res.get_json()["total"] == 0, "Expecting zero results when searching for a stopword"

        res = client.get("v0.1/search?query=water")
        assert res.status_code == 200
        first_result_count = res.get_json()["total"]
        assert first_result_count >= 2, "Expecting at least two result"

        res = client.get("v0.1/search?query=water en dijken")
        second_result_count = res.get_json()["total"]
        assert second_result_count >= 3, "Expecting at least three result"
        assert second_result_count > first_result_count, "Expecting more results because we search with OR filter"
        assert res.status_code == 200

    def test_geo_search_total(self, client):
        res = client.get(f"v0.1/search/geo?query={null_uuid}")
        assert res.status_code == 200
        assert "total" in res.get_json()
        assert "results" in res.get_json()

    def test_search_limit_offset(self, client):
        res = client.get("v0.1/search?query=water")
        assert res.status_code == 200
        assert len(res.get_json()['results']) == 10

        res = client.get("v0.1/search?query=water&limit=100")
        assert res.status_code == 200
        assert len(res.get_json()['results']) > 10

        res = client.get("v0.1/search?query=water&limit=3")
        assert res.status_code == 200
        assert len(res.get_json()['results']) == 3

        res = client.get("v0.1/search?query=water&limit=20&offset=5")
        assert res.status_code == 200
        assert len(res.get_json()['results']) == 20

        res = client.get("v0.1/search?query=water&limit=20&offset=-5")
        assert res.status_code == 403

        res = client.get("v0.1/search?query=water&limit=-1")
        assert res.status_code == 403
