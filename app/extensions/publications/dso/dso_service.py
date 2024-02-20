import io
import json
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from dso.builder.builder import Builder
from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.builder.state_manager.input_data.resource.policy_object.policy_object_repository import PolicyObjectRepository

from app.extensions.publications.dso.dso_assets_factory import DsoAssetsFactory
from app.extensions.publications.dso.dso_werkingsgebieden_factory import DsoWerkingsgebiedenFactory
from app.extensions.publications.dso.input_data_mapper import map_dso_input_data
from app.extensions.publications.dso.ow_helpers import create_updated_ambtsgebied_data
from app.extensions.publications.dso.template_parser import TemplateParser
from app.extensions.publications.exceptions import DSOStateExportError
from app.extensions.publications.models import Publication, PublicationBill, PublicationConfig, PublicationPackage
from app.extensions.publications.tables.ow import OWRegelingsgebiedTable
from app.extensions.source_werkingsgebieden.repository.werkingsgebieden_repository import WerkingsgebiedenRepository


class DSOService:
    """
    Interface for DSO service which converts our publication data
    to matching input for the DSO generator package.
    """

    def __init__(
        self,
        template_parsers: Dict[str, TemplateParser],
        dso_werkingsgebieden_factory: DsoWerkingsgebiedenFactory,
        dso_assets_factory: DsoAssetsFactory,
    ):
        self._template_parsers: Dict[str, TemplateParser] = template_parsers
        self._dso_werkingsgebieden_factory: DsoWerkingsgebiedenFactory = dso_werkingsgebieden_factory
        self._dso_assets_factory: DsoAssetsFactory = dso_assets_factory
        self._builder: Optional[Builder] = None
        self._input_data: Optional[InputData] = None
        self._state_exported: Optional[str] = None
        self._zip_buffer: Optional[io.BytesIO] = None

    def _get_object_template_repository(self, object_templates):
        repository = ObjectTemplateRepository(object_templates)
        return repository

    def _get_policy_object_repository(self, used_objects: List[dict]) -> PolicyObjectRepository:
        repository = PolicyObjectRepository()
        for o in used_objects:
            repository.add(o["Code"], o)
        return repository

    def _calculate_used_object_codes(self, free_text_template_str: str) -> Dict[str, bool]:
        """
        Calculate which object codes are used in the template.
        """
        soup = BeautifulSoup(free_text_template_str, "html.parser")
        objects = soup.find_all("object")
        codes = [obj.get("code") for obj in objects]
        codes_map = {code: True for code in codes}
        return codes_map

    def _filter_to_used_objects(self, objects: List[dict], used_object_codes: Dict[str, bool]) -> List[dict]:
        """
        Filter objects to only those that are specified in the template.
        """
        results: List[dict] = [o for o in objects if used_object_codes.get(o["Code"], False)]
        return results

    def prepare_publication_input(
        self,
        parser: TemplateParser,
        publication: Publication,
        bill: PublicationBill,
        package: PublicationPackage,
        config: PublicationConfig,
        objects,
        regelingsgebied: Optional[OWRegelingsgebiedTable],
    ) -> InputData:
        """
        Start point for converting our publication data to DSO input data.
        """
        free_text_template_str = parser.get_parsed_template(objects=objects)
        used_object_codes = self._calculate_used_object_codes(free_text_template_str)
        used_objects = self._filter_to_used_objects(objects, used_object_codes)

        # Initialize repositories
        object_template_repository = parser.get_object_template_repository()
        asset_repository = self._dso_assets_factory.get_repository_for_objects(used_objects)

        werkingsgebieden_objects: List[dict] = [o for o in objects if o["Object_Type"] == "werkingsgebied"]
        werkingsgebieden_repository: WerkingsgebiedenRepository = (
            self._dso_werkingsgebieden_factory.get_repository_for_objects(werkingsgebieden_objects, used_objects, True)
        )

        policy_object_repository = self._get_policy_object_repository(used_objects)

        if regelingsgebied:
            regelingsgebied_data = {
                "regelingsgebied": {"OW_ID": regelingsgebied.OW_ID, "ambtsgebied": regelingsgebied.Ambtsgebied}
            }
        else:
            regelingsgebied_data = create_updated_ambtsgebied_data(
                administative_borders_id=config.Administrative_Borders_ID,
                administative_borders_domain=config.Administrative_Borders_Domain,
                administrative_borders_date=config.Administrative_Borders_Date.strftime("%Y-%m-%d"),
            )

        input_data: InputData = map_dso_input_data(
            publication,
            bill,
            package,
            config,
            used_objects,
            free_text_template_str,
            object_template_repository,
            asset_repository,
            werkingsgebieden_repository,
            policy_object_repository,
            regelingsgebied_data,
        )

        self._input_data = input_data
        return input_data

    def state_filter(self, json_string):
        """
        Filter the exported state to strip redundant data such as
        resources to only UUIDs and specific fields
        """
        data = json.loads(json_string)

        try:
            resources = data["input_data"]["resources"]

            # Filter policy_object_repository to Code : UUID pair dict
            resources["policy_object_repository"] = {
                k: v["UUID"] for k, v in resources["policy_object_repository"].items()
            }

            # Filter asset_repository to only store UUIDs
            resources["asset_repository"] = list(resources["asset_repository"].keys())

            # Filter werkingsgebied_repository to only store UUIDs
            resources["werkingsgebied_repository"] = list(resources["werkingsgebied_repository"].keys())

            return json.dumps(data)
        except KeyError as e:
            raise DSOStateExportError(f"Trying to filter a non existing key in DSO state export. {e}")
        except Exception as e:
            raise DSOStateExportError(e)

    def get_exported_state(self) -> str:
        """
        Exported state from DSO generator.
        """
        return self._builder.export_json_state()

    def get_filtered_export_state(self) -> str:
        """
        Return DSO generator state filtered to smaller footprint for storage.
        """
        return self.state_filter(self.get_exported_state())

    def build_dso_package(self, input_data: Optional[InputData] = None, output_path: str = "./tmp"):
        """
        Triggers the DSO module to build the publication package from out input data.
        Saves the files to
        """
        self._builder = Builder(input_data or self._input_data)
        self._builder.build_publication_files()
        # Need file export still?
        # self._builder.save_files(output_path)
        self._zip_buffer: io.BytesIO = self._builder.zip_files()
