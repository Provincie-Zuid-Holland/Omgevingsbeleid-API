import io
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
from dso.models import DocumentType, OpdrachtType
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_object_repository
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.dependencies import depends_active_module
from app.extensions.playground.dependencies import (
    depends_dso_assets_factory,
    depends_dso_werkingsgebieden_factory,
    depends_input_data_service,
    depends_omgevingsvisie_template_parser,
    depends_programma_template_parser,
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
        programma_template_parser: TemplateParser,
        input_data_service: InputDataService,
        module: ModuleTable,
        document_type: DocumentType,
        opdracht_type: OpdrachtType,
        work_version: str,
        geo_new: bool,
    ):
        if document_type == DocumentType.OMGEVINGSVISIE:
            template_parser = omgevingsvisie_template_parser
        elif document_type == DocumentType.PROGRAMMA:
            template_parser = programma_template_parser

        self._db: Session = db
        self._object_repository: ObjectRepository = object_repository
        self._werkingsgebieden_factory: DsoWerkingsgebiedenFactory = werkingsgebieden_factory
        self._assets_factory: DsoAssetsFactory = assets_factory
        self._template_parser: TemplateParser = template_parser
        self._input_data_service: InputDataService = input_data_service
        self._module: ModuleTable = module
        self._document_type: DocumentType = document_type
        self._opdracht_type: OpdrachtType = opdracht_type
        self._work_version: str = work_version
        self._geo_new: bool = geo_new

    def handle(self) -> Response:
        repository = PublicationObjectRepository(self._db)
        objects = repository.fetch_objects(
            module_id=self._module.Module_ID,
            timepoint=datetime.utcnow(),
            object_types=self._template_parser.get_object_types(),
            field_map=self._template_parser.get_field_map(),
        )

        # @todo: remove
        # pretend all object have werkingsgebied-1 as werkingsgebied
        for i, o in enumerate(objects):
            if o["Object_Type"] not in ["beleidskeuze", "maatregel"]:
                continue
            objects[i]["Werkingsgebied_Code"] = "werkingsgebied-1"

        free_text_template_str = self._template_parser.get_parsed_template(objects)
        object_template_repository: ObjectTemplateRepository = self._template_parser.get_object_template_repository()

        used_object_codes = self._calculate_used_object_codes(free_text_template_str)
        used_objects = self._filter_to_used_objects(objects, used_object_codes)
        self._debug_invalid_objects(used_objects)

        asset_repository: DSOAssetRepository = self._assets_factory.get_repository_for_objects(used_objects)

        werkingsgebieden_objects: List[dict] = [o for o in objects if o["Object_Type"] == "werkingsgebied"]
        werkingsgebieden_repository: WerkingsgebiedRepository = (
            self._werkingsgebieden_factory.get_repository_for_objects(
                werkingsgebieden_objects, used_objects, self._geo_new
            )
        )

        input_data: InputData = self._input_data_service.create(
            self._document_type,
            self._opdracht_type,
            self._work_version,
            used_objects,
            free_text_template_str,
            object_template_repository,
            asset_repository,
            werkingsgebieden_repository,
        )

        builder = Builder(input_data)
        try:
            builder.build_publication_files()
            zip_buffer: io.BytesIO() = builder.zip_files()
        except Exception as e:
            a = True
            raise e

        # zip_filename = (
        #     f"download-dso-module-{self._module.Module_ID}-at-{datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S')}.zip"
        # )
        # zip_filename = input_data.publication_settings.opdracht.publicatie_bestand.replace(".xml", ".zip")
        zip_filename = "-".join(
            [
                "download",
                str(datetime.utcnow())[:10],
                self._document_type.value.lower(),
                self._opdracht_type.value.lower()[:3],
                self._work_version,
                str(input_data.publication_settings.opdracht.id_levering)[-6:],
            ]
        )
        zip_filename = f"{zip_filename}.zip"

        return Response(
            content=zip_buffer.read(),
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
        )

    def _debug_invalid_objects(self, used_objects: List[dict]):
        print("\n\n\n")
        for o in used_objects:
            if o.get("Description") is not None and (not "<p>" in o.get("Description")):
                print(o.get("Code"))
        print("\n\n\n")

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
            work_version: str,
            document_type: DocumentType,
            geo_new: bool = True,
            opdracht_type: OpdrachtType = OpdrachtType.VALIDATIE,
            db: Session = Depends(depends_db),
            object_repository: ObjectRepository = Depends(depends_object_repository),
            werkingsgebieden_factory: DsoWerkingsgebiedenFactory = Depends(depends_dso_werkingsgebieden_factory),
            assets_factory: DsoAssetsFactory = Depends(depends_dso_assets_factory),
            omgevingsvisie_template_parser: TemplateParser = Depends(depends_omgevingsvisie_template_parser),
            programma_template_parser: TemplateParser = Depends(depends_programma_template_parser),
            input_data_service: InputDataService = Depends(depends_input_data_service),
            module: ModuleTable = Depends(depends_active_module),
        ) -> Response:
            handler: EndpointHandler = EndpointHandler(
                db,
                object_repository,
                werkingsgebieden_factory,
                assets_factory,
                omgevingsvisie_template_parser,
                programma_template_parser,
                input_data_service,
                module,
                document_type,
                opdracht_type,
                work_version,
                geo_new,
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
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")

        return DoDsoEndpoint(path)