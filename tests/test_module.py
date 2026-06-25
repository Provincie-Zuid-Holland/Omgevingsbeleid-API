# class TestModule:
#     def test_post_module(self, client, db_session, test_super_user_access_auth_header):
#         data = {
#             'Title': 'Test module',
#             'Description': 'Test description',
#             'Module_Manager_1_UUID': '11111111-0000-0000-0000-000000000001',
#             'Module_Manager_2_UUID': '11111111-0000-0000-0000-000000000002',
#         }
#         response = client.post('/modules', headers=test_super_user_access_auth_header, json=data)
#         assert response.status_code == 200
#
#     def test_get_module(self, client, test_super_user_access_auth_header):
#         response = client.get('/modules', headers=test_super_user_access_auth_header)
#         assert response.status_code == 200
#         json_response = response.json()
#         assert len(json_response["results"]) == 1
