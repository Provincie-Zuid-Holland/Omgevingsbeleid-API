import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set
from uuid import UUID

import dso.models as dso_models
from bs4 import BeautifulSoup
from dso.builder.builder import Builder
from dso.builder.state_manager.input_data.besluit import Artikel, Besluit
from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.builder.state_manager.input_data.regeling import Regeling
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository as DSOAssetRepository
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
from app.extensions.html_assets.db.tables import AssetsTable
from app.extensions.html_assets.dependencies import depends_asset_repository
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.playground.dependencies import depends_dso_werkingsgebieden_factory
from app.extensions.playground.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.playground.services.dso_werkingsgebieden_factory import DsoWerkingsgebiedenFactory

jinja_template = """

<div><object code="visie_algemeen-1" /></div>
<div><object code="visie_algemeen-2" /></div>
<div><object code="visie_algemeen-3" /></div>

<div>
    <h1>Ambities van Zuid-Holland</h1>
    {%- for a in ambitie | sort(attribute='Title') %}
        <div data-hint-element="divisietekst"><object code="{{ a.Code }}" template="ambitie" /></div>
    {%- endfor %}
</div>

<div>
    <h1>Beleidsdoelen en beleidskeuzes</h1>

    {%- for d in beleidsdoel | sort(attribute='Title') %}
        <div>
            <object code="{{ d.Code }}" template="beleidsdoel" />

            {% set filtered_results = beleidskeuze | selectattr('Hierarchy_Code', 'equalto', d.Code) | list %}
            {% if filtered_results %}
            <div>
                <h1>Beleidskeuzes van {{ d.Title }}</h1>
                {%- for k in filtered_results | sort(attribute='Title') %}
                <div><object code="{{ k.Code }}" template="beleidskeuze" /></div>
                {%- endfor %}
            </div>
            {% endif %}
        </div>
    {%- endfor %}
</div>

"""


def create_vrijetekst_template():
    return jinja_template


def get_policy_object_repository(used_objects: List[dict]) -> PolicyObjectRepository:
    repository = PolicyObjectRepository()

    for o in used_objects:
        repository.add(o["Code"], o)

    return repository


def get_asset_repository(assets: List[AssetsTable]) -> DSOAssetRepository:
    repository = DSOAssetRepository()

    for asset in assets:
        asset_dict = {
            "UUID": str(asset.UUID),
            "Created_Date": str(asset.Created_Date),
            "Meta": json.loads(asset.Meta),
            "Content": asset.Content,
        }
        repository.add(asset_dict)

    return repository


def get_werkingsgebied_repository(werkingsgebieden: List[dict]):
    repository = WerkingsgebiedRepository("pv28", "nld")
    for werkingsgebied in werkingsgebieden:
        repository.add(werkingsgebied)
    return repository


object_templates = {
    "visie_algemeen": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description | default('', true) }}
""",
    "ambitie": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description | default('', true) }}
""",
    "beleidsdoel": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description | default('', true) }}
""",
    "beleidskeuze": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{% if o.Gebied_UUID is not none %}
<!--[GEBIED-UUID:{{o.Gebied_UUID}}]-->
{% endif %}

{% if o.Description %}
<h2>Wat wil de provincie bereiken?</h2>
{{ o.Description }}
{% endif %}

{% if o.Cause %}
<h2>Aanleiding</h2>
{{ o.Cause }}
{% endif %}

{% if o.Provincial_Interest %}
<h2>Motivering Provinciaal Belang</h2>
{{ o.Provincial_Interest }}
{% endif %}

{% if o.Explanation %}
<h2>Nadere uitwerking</h2>
{{ o.Explanation }}
{% endif %}
""",
}


def get_object_template_repository():
    repository = ObjectTemplateRepository(object_templates)
    return repository


def get_input_data(
    used_objects: List[dict],
    vrijetekst_template: str,
    assets: List[AssetsTable],
    werkingsgebieden: List[dict],
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
            policy_object_repository=get_policy_object_repository(used_objects),
            asset_repository=get_asset_repository(assets),
            werkingsgebied_repository=get_werkingsgebied_repository(werkingsgebieden),
        ),
        object_template_repository=get_object_template_repository(),
    )

    return input_data


def calculate_used_object_codes(vrijetekst_template_str: str) -> Dict[str, bool]:
    soup = BeautifulSoup(vrijetekst_template_str, "html.parser")
    objects = soup.find_all("object")
    codes = [obj.get("code") for obj in objects]
    codes_map = {code: True for code in codes}
    return codes_map


def filter_to_used_objects(objects: List[dict], used_object_codes: Dict[str, bool]) -> List[dict]:
    results: List[dict] = [o for o in objects if used_object_codes.get(o["Code"], False)]
    return results


asset_re = re.compile("^\[ASSET")


def calculate_asset_uuids(objects: List[dict]) -> List[UUID]:
    asset_uuids: Set[UUID] = set()

    asset_fields = [
        "Description",
        "Cause",
        "Provincial_Interest",
        "Explanation",
    ]

    for o in objects:
        for field in asset_fields:
            value = o.get(field, None)
            if value is None:
                continue

            soup = BeautifulSoup(value, "html.parser")
            for img in soup.find_all("img", src=asset_re):
                try:
                    asset_uuid = UUID(img["src"].split(":")[1][:-1])
                    asset_uuids.add(asset_uuid)
                except ValueError:
                    continue

    return list(asset_uuids)


def calculate_werkingsgebieden_uuids(objects: List[dict]) -> List[UUID]:
    uuids: Set[UUID] = set([o.get("Gebied_UUID") for o in objects if o.get("Gebied_UUID", None) is not None])
    return list(uuids)


def fetch_werkingsgebieden(
    werkingsgebieden_factory: DsoWerkingsgebiedenFactory, werkingsgebied_uuids: List[UUID]
) -> List[dict]:
    werkingsgebieden: List[dict] = []
    for werkingsgebied_uuid in werkingsgebied_uuids:
        werkingsgebied = werkingsgebieden_factory.get(werkingsgebied_uuid)
        werkingsgebieden.append(werkingsgebied)

    return werkingsgebieden


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_repository: ObjectRepository,
        asset_repository: AssetRepository,
        werkingsgebieden_factory: DsoWerkingsgebiedenFactory,
    ):
        self._db: Session = db
        self._object_repository: ObjectRepository = object_repository
        self._asset_repository: AssetRepository = asset_repository
        self._werkingsgebieden_factory: DsoWerkingsgebiedenFactory = werkingsgebieden_factory

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

        aggregated_objects = defaultdict(list)
        for o in objects:
            aggregated_objects[o["Object_Type"]].append(o)

        base_template = Template(jinja_template)
        vrijetekst_template_str = base_template.render(
            **aggregated_objects,
        )
        vrijetekst_template_str = vrijetekst_template_str.strip()
        vrijetekst_template_str = vrijetekst_template_str.replace("\n", "")

        used_object_codes = calculate_used_object_codes(vrijetekst_template_str)
        used_objects = filter_to_used_objects(objects, used_object_codes)

        asset_uuids = calculate_asset_uuids(objects)
        assets: List[AssetsTable] = self._asset_repository.get_by_uuids(asset_uuids)

        werkingsgebieden_uuids = calculate_werkingsgebieden_uuids(objects)
        werkingsgebieden = fetch_werkingsgebieden(self._werkingsgebieden_factory, werkingsgebieden_uuids)

        input_data: InputData = get_input_data(
            used_objects,
            vrijetekst_template_str,
            assets,
            werkingsgebieden,
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
            asset_repository: AssetRepository = Depends(depends_asset_repository),
            werkingsgebieden_factory: DsoWerkingsgebiedenFactory = Depends(depends_dso_werkingsgebieden_factory),
        ) -> FileResponse:
            handler: EndpointHandler = EndpointHandler(
                db, object_repository, asset_repository, werkingsgebieden_factory
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
