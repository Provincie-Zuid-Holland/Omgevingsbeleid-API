#     def state_filter(self, json_string):
#         """
#         Filter the exported state to strip redundant data such as
#         resources to only UUIDs and specific fields
#         """
#         data = json.loads(json_string)
#         del data["output_files"]

#         try:
#             resources = data["input_data"]["resources"]

#             # Filter policy_object_repository to Code : UUID pair dict
#             resources["policy_object_repository"] = {
#                 k: v["UUID"] for k, v in resources["policy_object_repository"].items()
#             }

#             # Filter asset_repository to only store UUIDs
#             resources["asset_repository"] = list(resources["asset_repository"].keys())

#             # Filter werkingsgebied_repository to only store UUIDs
#             resources["werkingsgebied_repository"] = list(resources["werkingsgebied_repository"].keys())

#             return json.dumps(data)
#         except KeyError as e:
#             raise DSOStateExportError(f"Trying to filter a non existing key in DSO state export. {e}")
#         except Exception as e:
#             raise DSOStateExportError(e)

#     def get_filtered_export_state(self) -> str:
#         state = self._builder.export_json_state()
#         result = self.state_filter(state)
#         return result

#     def build_dso_package(self, input_data: Optional[InputData] = None, output_path: str = "./tmp"):
#         self._builder = Builder(input_data or self._input_data)
#         self._builder.build_publication_files()
#         self._zip_buffer: io.BytesIO = self._builder.zip_files()
