from datetime import datetime
from typing import Dict, List

from bs4 import BeautifulSoup
from dso.builder.builder import Builder
from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository as DSOAssetRepository
from dso.builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_object_repository
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.playground.dependencies import (
    depends_dso_assets_factory,
    depends_dso_werkingsgebieden_factory,
    depends_input_data_service,
    depends_omgevingsvisie_template_parser,
)
from app.extensions.playground.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.playground.services.dso_assets_factory import DsoAssetsFactory
from app.extensions.playground.services.dso_werkingsgebieden_factory import DsoWerkingsgebiedenFactory
from app.extensions.playground.services.input_data_service import InputDataService
from app.extensions.playground.services.template_parser import TemplateParser


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_repository: ObjectRepository,
        werkingsgebieden_factory: DsoWerkingsgebiedenFactory,
        assets_factory: DsoAssetsFactory,
        omgevingsvisie_template_parser: TemplateParser,
        input_data_service: InputDataService,
    ):
        self._db: Session = db
        self._object_repository: ObjectRepository = object_repository
        self._werkingsgebieden_factory: DsoWerkingsgebiedenFactory = werkingsgebieden_factory
        self._assets_factory: DsoAssetsFactory = assets_factory
        self._omgevingsvisie_template_parser: TemplateParser = omgevingsvisie_template_parser
        self._input_data_service: InputDataService = input_data_service

    def handle(self) -> FileResponse:
        repository = PublicationObjectRepository(self._db)
        objects = repository.fetch_objects(
            module_id=1,
            timepoint=datetime.utcnow(),
            object_types=[
                "visie_algemeen",
                "ambitie",
                "beleidsdoel",
                "beleidskeuze",
            ],
            field_map=[
                "UUID",
                "Object_Type",
                "Object_ID",
                "Code",
                "Hierarchy_Code",
                "Gebied_UUID",
                "Title",
                "Description",
                "Cause",
                "Provincial_Interest",
                "Explanation",
            ],
        )

        free_text_template_str = self._omgevingsvisie_template_parser.get_parsed_template(objects)
        object_template_repository: ObjectTemplateRepository = (
            self._omgevingsvisie_template_parser.get_object_template_repository()
        )

        used_object_codes = self._calculate_used_object_codes(free_text_template_str)
        used_objects = self._filter_to_used_objects(objects, used_object_codes)

        asset_repository: DSOAssetRepository = self._assets_factory.get_repository_for_objects(used_objects)
        werkingsgebieden_repository: WerkingsgebiedRepository = (
            self._werkingsgebieden_factory.get_repository_for_objects(objects)
        )

        input_data: InputData = self._input_data_service.create(
            used_objects,
            free_text_template_str,
            object_template_repository,
            asset_repository,
            werkingsgebieden_repository,
        )

        builder = Builder(input_data)
        builder.build_publication_files()
        builder.save_files("./output-dso")

        a = True

    def _calculate_used_object_codes(self, free_text_template_str: str) -> Dict[str, bool]:
        soup = BeautifulSoup(free_text_template_str, "html.parser")
        objects = soup.find_all("object")
        codes = [obj.get("code") for obj in objects]
        codes_map = {code: True for code in codes}
        return codes_map

    def _filter_to_used_objects(self, objects: List[dict], used_object_codes: Dict[str, bool]) -> List[dict]:
        results: List[dict] = [o for o in objects if used_object_codes.get(o["Code"], False)]
        return results


class DoDsoEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            db: Session = Depends(depends_db),
            object_repository: ObjectRepository = Depends(depends_object_repository),
            werkingsgebieden_factory: DsoWerkingsgebiedenFactory = Depends(depends_dso_werkingsgebieden_factory),
            assets_factory: DsoAssetsFactory = Depends(depends_dso_assets_factory),
            omgevingsvisie_template_parser: TemplateParser = Depends(depends_omgevingsvisie_template_parser),
            input_data_service: InputDataService = Depends(depends_input_data_service),
        ) -> FileResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                object_repository,
                werkingsgebieden_factory,
                assets_factory,
                omgevingsvisie_template_parser,
                input_data_service,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            summary=f"Download DSO",
            description=None,
            tags=["Playground"],
        )

        return router


class DoDsoEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "playground_do_dso"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return DoDsoEndpoint(path)
