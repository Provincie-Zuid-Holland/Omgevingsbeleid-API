from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from dso.builder.builder import Builder
from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository
from dso.builder.state_manager.input_data.resource.policy_object.policy_object_repository import PolicyObjectRepository
from dso.builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)

from app.extensions.publications.dso.dso_assets_factory import DsoAssetsFactory
from app.extensions.publications.dso.dso_werkingsgebieden_factory import DsoWerkingsgebiedenFactory
from app.extensions.publications.dso.input_data_mapper import map_dso_input_data
from app.extensions.publications.dso.template_parser import TemplateParser


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

        self._input_data: Optional[InputData] = None
        self._state_exported: Optional[str] = None

    def get_object_template_repository(self, object_templates):
        repository = ObjectTemplateRepository(object_templates)
        return repository

    def get_policy_object_repository(self, used_objects: List[dict]) -> PolicyObjectRepository:
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

    def prepare_publication_input(self, bill, package, config, objects):
        """
        Start point for converting our publication data to DSO input data.
        """

        # Build parsed object templates
        free_text_template_str = self._template_parsers["Omgevingsvisie"].get_parsed_template(objects=objects)
        used_object_codes = self._calculate_used_object_codes(free_text_template_str)
        used_objects = self._filter_to_used_objects(objects, used_object_codes)

        # Initialize repositories
        object_template_repository: ObjectTemplateRepository = self._template_parsers[
            "Omgevingsvisie"
        ].get_object_template_repository()

        asset_repository: AssetRepository = self._dso_assets_factory.get_repository_for_objects(used_objects)

        werkingsgebieden_repository: WerkingsgebiedRepository = (
            self._dso_werkingsgebieden_factory.get_repository_for_objects(objects)
        )

        policy_object_repository: PolicyObjectRepository = self.get_policy_object_repository(used_objects)

        # Convert to INput data
        input_data: InputData = map_dso_input_data(
            bill,
            package,
            config,
            used_objects,
            free_text_template_str,
            object_template_repository,
            asset_repository,
            werkingsgebieden_repository,
            policy_object_repository,
        )

        self._input_data = input_data
        return input_data

    def build_dso_package(self, input_data: Optional[InputData] = None, output_path: str = "./output-dso"):
        """
        Build DSO package from input data and export generator State.
        """
        builder = Builder(input_data or self._input_data)
        builder.build_publication_files()
        builder.save_files(output_path)
        # Return json output of state
        exported_state = builder.export_json_state()
        return exported_state
