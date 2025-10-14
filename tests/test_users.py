from conftest import mock_select_result, fake_user


class TestUsers:
    def test_users_list(self, mock_db_session, client):
        data = [
            {
                "UUID": fake_user.UUID,
                "Gebruikersnaam": fake_user.Gebruikersnaam,
                "Email": fake_user.Email,
                "Rol": fake_user.Rol,
                "Status": fake_user.Status,
                "IsActive": True,
            },
            {
                "UUID": "11111111-0000-0000-0000-000000000002",
                "Gebruikersnaam": "user",
                "Email": "user@example.com",
                "Rol": "Behandelend Ambtenaar",
                "Status": "Actief",
                "IsActive": True,
            },
        ]
        mock_select_result(mock_db_session, data)

        response = client.get("/users")
        assert response.status_code == 200, response.text
        json_response = response.json()
        assert len(json_response['results']) == 2
