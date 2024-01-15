from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import dso.models as dso_models
from dso.builder.builder import Builder
from dso.builder.state_manager.input_data.besluit import Artikel, Besluit
from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.builder.state_manager.input_data.regeling import Regeling
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository
from dso.builder.state_manager.input_data.resource.policy_object.policy_object_repository import PolicyObjectRepository
from dso.builder.state_manager.input_data.resource.resources import Resources
from dso.builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from jinja2 import Template
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_object_repository
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.playground.services.publication_object_repository import PublicationObjectRepository

jinja_template = """

<div><object code="visie_algemeen-1" /></div>
<div><object code="visie_algemeen-2" /></div>

<div>
    <div>
        <object code="visie_algemeen-3" />
    </div>
    <div>
        <h1>Ambities van Zuid-Holland</h1>
        {%- for a in ambitie | sort(attribute='Title') %}
            <div>
                <object code="{{ a.Code }}" template="ambitie" />
            </div>
        {%- endfor %}
    </div>
</div>

<div>
    <h1>Beleidsdoelen en beleidskeuzes</h1>

</div>

"""


def create_vrijetekst_template():
    return jinja_template


def get_policy_object_repository(aggregated_objects: Dict[str, List[dict]]):
    repository = PolicyObjectRepository()

    for objects in aggregated_objects.values():
        for o in objects:
            repository.add(o["Code"], o)

    #     repository.add("visie_algemeen-1", {
    #         "Object_Type": "visie_algemeen",
    #         "Object_ID": 1,
    #         "Code": "visie_algemeen-1",
    #         "Title": "Inleiding",
    #         "Description": """<h3>Leeswijzer</h3>
    # <p>De Zuid-Hollandse leefomgeving verbeteren, elke dag, dat is waar de provincie
    # aan werkt.<p>"""
    #     })

    #     repository.add("visie_algemeen-2", {
    #         "Object_Type": "visie_algemeen",
    #         "Object_ID": 2,
    #         "Object_Code": "visie_algemeen-2",
    #         "Title": "Sturingsfilosofie",
    #         "Description": """<h3>Ruimte voor ontwikkeling</h3>
    # <p>De provincie Zuid-Holland heeft met haar uitgebreide instrumentarium grote
    # meerwaarde bij het oplossen van de maatschappelijke opgaven van vandaag en
    # morgen. En met inbreng van kennis en creativiteit vanuit de samenleving kan nog
    # meer worden bereikt. De kunst is het oplossend vermogen van de maatschappij
    # te stimuleren en te benutten. Alleen ga je sneller, samen kom je verder</p>"""
    #     })

    #     repository.add("visie_algemeen-3", {
    #         "Object_Type": "visie_algemeen",
    #         "Object_ID": 3,
    #         "Object_Code": "visie_algemeen-3",
    #         "Title": "Hier staat Zuid-Holland nu",
    #         "Description": """<h3>Leeswijzer</h3>
    # <p>De huidige staat van de leefomgeving van Zuid-Holland beschrijven we aan de
    # hand van twee onderdelen:</p>
    # <ul><li><p>Een beschrijving van de KWALITEITEN VAN ZUID-HOLLAND: de drie
    # deltalandschappen, de Zuid-Hollandse steden en de strategische ligging in
    # internationale netwerken.</p></li>
    # <li><p>Een beschrijving van de huidige staat van de LEEFOMGEVING op basis van de
    # leefomgevingstoets.</p></li></ul>"""
    #     })

    return repository


def get_asset_repository():
    repository = AssetRepository()
    return repository


def get_werkingsgebied_repository():
    repository = WerkingsgebiedRepository("pv28", "nld")
    return repository


object_templates = {
    "visie_algemeen": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description }}
""",
    "ambitie": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description }}
""",
}


def get_object_template_repository():
    repository = ObjectTemplateRepository(object_templates)
    return repository


def get_input_data(
    aggregated_objects: Dict[str, List[dict]],
    vrijetekst_template: str,
):
    input_data = InputData(
        publication_settings=dso_models.PublicationSettings(
            document_type="VISIE",
            datum_bekendmaking="2024-02-14",
            datum_juridisch_werkend_vanaf="2024-02-15",
            provincie_id="pv28",
            wId_suffix="1",
            soort_bestuursorgaan="/tooi/def/thes/kern/c_411b4e4a",
            expression_taal="nld",
            regeling_componentnaam="nieuweregeling",
            provincie_ref="/tooi/id/provincie/pv28",
            opdracht={
                "opdracht_type": "VALIDATIE",
                "id_levering": "c43e95c5-6d8d-4132-bfa7-9507f8fb9cd2",
                "id_bevoegdgezag": "00000001002306608000",
                "id_aanleveraar": "00000001002306608000",
                "publicatie_bestand": "akn_nl_bill_pv28-2-89.xml",
                "datum_bekendmaking": "2024-02-14",
            },
            doel=dso_models.Doel(jaar="2024", naam="InstellingOmgevingsvisie"),
            besluit_frbr={
                "work_land": "nl",
                "work_datum": "2024",
                "work_overig": "2_2093",
                "expression_taal": "nld",
                "expression_datum": "2024-01-05",
                "expression_versie": "2093",
                "expression_overig": None,
            },
            regeling_frbr={
                "work_land": "nl",
                "work_datum": "2024",
                "work_overig": "2_89",
                "expression_taal": "nld",
                "expression_datum": "2024-01-05",
                "expression_versie": "89",
                "expression_overig": None,
            },
        ),
        besluit=Besluit(
            officiele_titel="Opschrift besluit - Dossier naam Hello World Programma",
            regeling_opschrift="Omgevingsprogramma Provincie Zuid-Holland",
            aanhef="Om de Omgevingsvisie Provincie Zuid-Holland beschikbaar te maken in het Digitale Stelsel van de Omgevingswet is het noodzakelijk dat de reeds vastgestelde Omgevingsvisie Zuid-Holland opnieuw wordt gepubliceerd en bekend gemaakt.",
            wijzig_artikel=Artikel(
                label="Artikel",
                inhoud='Zoals is aangegeven in <IntRef ref="cmp_A">Bijlage A bij Artikel I</IntRef>',
            ),
            tekst_artikelen=[],
            tijd_artikel=Artikel(
                label="Artikel",
                inhoud="Dit besluit treedt in werking op de dag waarop dit bekend wordt gemaakt.",
            ),
            sluiting="Gegeven te 's-Gravenhage, 15 februari 2024",
            ondertekening="Gedupeerde Staten",
            rechtsgebieden=[
                "Omgevingsrecht",
            ],
            onderwerpen=["ruimtelijke_ordening"],
            soort_procedure="Definitief_besluit",
        ),
        regeling=Regeling(
            versienummer="1",
            officiele_titel="Dossier naam Hello World Programma",
            citeertitel="Citeertitel omgevingsprogramma hello World",
            is_officieel="true",
            rechtsgebieden=[
                "Omgevingsrecht",
            ],
            onderwerpen=["ruimtelijke_ordening"],
        ),
        regeling_vrijetekst=vrijetekst_template,
        procedure_verloop=dso_models.ProcedureVerloop(
            bekend_op="2024-02-14",
            stappen=[
                dso_models.ProcedureStap(
                    soort_stap="/join/id/stop/procedure/stap_002",
                    voltooid_op="2024-01-05",
                ),
                dso_models.ProcedureStap(
                    soort_stap="/join/id/stop/procedure/stap_003",
                    voltooid_op="2024-01-06",
                ),
            ],
        ),
        resources=Resources(
            policy_object_repository=get_policy_object_repository(aggregated_objects),
            asset_repository=get_asset_repository(),
            werkingsgebied_repository=get_werkingsgebied_repository(),
        ),
        object_template_repository=get_object_template_repository(),
    )

    return input_data


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_repository: ObjectRepository,
    ):
        self._db: Session = db
        self._object_repository: ObjectRepository = object_repository

    def handle(self) -> FileResponse:
        repository = PublicationObjectRepository(self._db)
        objects = repository.fetch_objects(
            module_id=1,
            timepoint=datetime.utcnow(),
            object_types=[
                "visie_algemeen",
                "ambitie",
                "beleidskeuze",
            ],
            field_map=[
                "UUID",
                "Object_Type",
                "Object_ID",
                "Code",
                "Title",
                "Description",
                "Hierarchy_Code",
            ],
        )

        aggregated_objects = defaultdict(list)
        for o in objects:
            aggregated_objects[o["Object_Type"]].append(o)

        base_template = Template(jinja_template)
        vrijetekst_template = base_template.render(
            **aggregated_objects,
        )

        input_data: InputData = get_input_data(
            aggregated_objects,
            vrijetekst_template,
        )

        builder = Builder(input_data)
        builder.build_publication_files()
        builder.save_files("./output-dso")

        a = True


class DoDsoEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            db: Session = Depends(depends_db),
            object_repository: ObjectRepository = Depends(depends_object_repository),
        ) -> FileResponse:
            handler: EndpointHandler = EndpointHandler(db, object_repository)
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
