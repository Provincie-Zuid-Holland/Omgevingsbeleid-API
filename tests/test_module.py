from datetime import timezone, datetime

from conftest import mock_select_result


class TestModule:
    def test_post_modules(self, client, mock_db_session):
        def fake_flush():
            for obj in mock_db_session.add.call_args_list:
                instance = obj[0][0]
                if hasattr(instance, "Module_ID"):
                    instance.Module_ID = 100

        mock_db_session.flush.side_effect = fake_flush

        data = {
            "Title": "Test module",
            "Description": "Test description",
            "Module_Manager_1_UUID": "11111111-0000-0000-0000-000000000001",
            "Module_Manager_2_UUID": "11111111-0000-0000-0000-000000000002",
        }
        response = client.post("/modules", json=data)
        assert response.status_code == 200
        assert response.json()["Module_ID"] == 100

    def test_get_modules(self, client, mock_db_session):
        data = {
            "Module_ID": 1,
            "Title": "Some module",
            "Description": "Some module description",
            "Created_Date": datetime.now(timezone.utc),
            "Modified_Date": datetime.now(timezone.utc),
            "Created_By_UUID": "11111111-0000-0000-0000-000000000001",
            "Modified_By_UUID": "11111111-0000-0000-0000-000000000002",
            "Activated": 0,
            "Closed": 0,
            "Successful": 0,
            "Temporary_Locked": 0,
            "Module_Manager_1_UUID": "11111111-0000-0000-0000-000000000003",
        }
        mock_select_result(mock_db_session, [data])
        response = client.get("/modules")
        assert response.status_code == 200
        json_response = response.json()
        assert len(json_response["results"]) == 1
        assert json_response["results"][0]["Title"] == "Some module"