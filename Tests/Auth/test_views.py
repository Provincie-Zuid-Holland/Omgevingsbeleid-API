# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import json
from flask_jwt_extended import decode_token


class TestAuthView:
    def test_login_missing_parameters(self, client):
        resp = client.post("/v0.1/login")
        assert resp.status_code == 400, f"Status code was {resp.status_code}, should be 400."
        assert resp.get_json()["message"] == "Identifier en password parameter niet gevonden"


    def test_login_missing_identifier(self, client):
        resp = client.post("/v0.1/login", json={"password": "password"})
        assert resp.status_code == 400, f"Status code was {resp.status_code}, should be 400."
        assert resp.get_json()["message"] == "Identifier parameter niet gevonden"


    def test_login_missing_password(self, client):
        resp = client.post("/v0.1/login", json={"identifier": "user@example.com"})
        assert resp.status_code == 400, f"Status code was {resp.status_code}, should be 400."
        assert resp.get_json()["message"] == "Password parameter niet gevonden"


    def test_login_unknown_user(self, client):
        resp = client.post("/v0.1/login", json={"identifier": "unknown@example.com", "password": "password"})
        assert resp.status_code == 401, f"Status code was {resp.status_code}, should be 401."
        assert resp.get_json()["message"] == "Wachtwoord of gebruikersnaam ongeldig"


    def test_login_invalid_combination(self, client):
        resp = client.post("/v0.1/login", json={"identifier": "admin@example.com", "password": "wrong-password"})
        assert resp.status_code == 401, f"Status code was {resp.status_code}, should be 401."
        assert resp.get_json()["message"] == "Wachtwoord of gebruikersnaam ongeldig"


    def test_login_success(self, client):
        resp = client.post("/v0.1/login", json={"identifier": "admin@example.com", "password": "password"})
        assert resp.status_code == 200, f"Status code was {resp.status_code}, should be 200."

        data = resp.get_json()
        for key in ["access_token", "expires", "identifier", "deployment type"]:
                assert key in data, f"Missing property '{key}' in response object."

        # validate the token
        raw_token = decode_token(data["access_token"])
        assert "UUID" in raw_token["identity"], "UUID should be in the identity"
        assert len(raw_token["identity"]["UUID"]) == 36, "UUID should be valid"
        assert raw_token["identity"]["Email"] == "admin@example.com", "Email should be the one that you logged in with"
        assert not "Wachtwoord" in raw_token["identity"], "Wachtwoord should not be stored in the identity"

    
    def test_password_reset_no_jwt(self, client):
        resp = client.post("/v0.1/password-reset", json={"password": "password", "new_password": "new_password"})
        assert resp.status_code == 401, f"Status code was {resp.status_code}, should be 401."
        assert resp.get_json()["message"] == "Authorisatie niet geldig: 'Missing Authorization Header'"


    def test_password_reset_missing_password(self, client_admin):
        resp = client_admin.post("/v0.1/password-reset", json={"new_password": "new_password"})
        assert resp.status_code == 400, f"Status code was {resp.status_code}, should be 400."
        assert resp.get_json()["message"] == "password parameter not found"


    def test_password_reset_missing_new_password(self, client_admin):
        resp = client_admin.post("/v0.1/password-reset", json={"password": "password"})
        assert resp.status_code == 400, f"Status code was {resp.status_code}, should be 400."
        assert resp.get_json()["message"] == "new_password parameter not found"


    def test_password_reset_new_password_too_weak(self, client_admin):
        resp = client_admin.post("/v0.1/password-reset", json={"password": "password", "new_password": "hello"})
        assert resp.status_code == 400, f"Status code was {resp.status_code}, should be 400."
        assert resp.get_json()["message"] == "Password does not meet requirements"
        assert len(resp.get_json()["errors"]) == 4, "We are expecting 4 password policy errors"


    def test_password_reset_new_password_little_weak(self, client_admin):
        resp = client_admin.post("/v0.1/password-reset", json={"password": "password", "new_password": "Hellonewpassword1"})
        assert resp.status_code == 400, f"Status code was {resp.status_code}, should be 400."
        assert resp.get_json()["message"] == "Password does not meet requirements"
        assert len(resp.get_json()["errors"]) == 1, "We are expecting 1 password policy error"


    def test_password_reset_invalid_current_password(self, client_admin):
        resp = client_admin.post("/v0.1/password-reset", json={"password": "wrong-password", "new_password": "Hell0newp@ssword"})
        assert resp.status_code == 401, f"Status code was {resp.status_code}, should be 401."
        assert resp.get_json()["message"] == "Unable to find user"


    def test_password_reset_login_after_reset(self, client):
        # as we use the raw client we need to login first
        resp = client.post("/v0.1/login", json={"identifier": "alex@example.com", "password": "password"})
        assert resp.status_code == 200, f"Status code was {resp.status_code}, should be 200."

        access_token = resp.get_json()["access_token"]

        # now we are going to change the password
        resp = client.post("/v0.1/password-reset",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"password": "password", "new_password": "Hell0newp@ssword"},
        )
        assert resp.status_code == 200, f"Status code was {resp.status_code}, should be 200."
        assert resp.get_json()["message"] == "Password changed"

        # logging in with the old password should fail
        resp = client.post("/v0.1/login", json={"identifier": "alex@example.com", "password": "password"})
        assert resp.status_code == 401, f"Status code was {resp.status_code}, should be 401."

        # logging in with the new password should succeed
        resp = client.post("/v0.1/login", json={"identifier": "alex@example.com", "password": "Hell0newp@ssword"})
        assert resp.status_code == 200, f"Status code was {resp.status_code}, should be 200."
