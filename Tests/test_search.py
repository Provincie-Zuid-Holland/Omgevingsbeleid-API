# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import pytest

from Api.settings import null_uuid


@pytest.mark.usefixtures("fixture_data", "wait_for_fulltext_index")
class TestSearch:
    def test_fieldset(self, client):
        res = client.get("v0.1/search?query=water")
        assert res.status_code == 200

        data = res.get_json()
        assert len(data["results"]) > 0, "Expecting at least one result"
        assert list(data["results"][0].keys()) == [
            "Omschrijving",
            "RANK",
            "Titel",
            "Type",
            "UUID",
        ]

    def test_keywords(self, client):
        res = client.get("v0.1/search?query=energie")
        assert res.status_code == 200
        data = res.get_json()
        print(data)

        res = client.get("v0.1/search?query=energie en lopen")
        assert res.status_code == 200
        data = res.get_json()
        print(data)

    def test_search_total(self, client):
        res = client.get("v0.1/search?query=water")
        assert res.status_code == 200
        assert 'total' in res.get_json()
        assert 'results' in res.get_json()

    def test_geo_search_total(self, client):
        res = client.get(f"v0.1/search/geo?query={null_uuid}")
        assert res.status_code == 200
        assert 'total' in res.get_json()
        assert 'results' in res.get_json()

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
