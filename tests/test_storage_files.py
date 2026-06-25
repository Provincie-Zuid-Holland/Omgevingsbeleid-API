class TestStorageFiles:
    def test_users_list(self, client, test_super_user_access_auth_header):
        response = client.get("/storage-files", headers=test_super_user_access_auth_header)
        assert response.status_code == 200
        json_response = response.json()
        assert len(json_response['results']) == 2