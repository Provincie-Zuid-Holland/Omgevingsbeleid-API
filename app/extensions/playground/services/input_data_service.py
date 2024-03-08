import math
import uuid
from datetime import datetime
from typing import List

import dso.models as dso_models
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
from dso.models import DocumentType, OpdrachtType


class InputDataService:
    def create(
        self,
        document_type: DocumentType,
        opdracht_type: OpdrachtType,
        work_version: str,
        used_objects: List[dict],
        free_text_template_str: str,
        object_template_repository: ObjectTemplateRepository,
        asset_repository: DSOAssetRepository,
        werkingsgebied_repository: WerkingsgebiedRepository,
    ) -> InputData:
        document_type_title: str = document_type.value.lower()
        date = datetime.utcnow()
        datum = str(date)[0:10]
        jaar = str(date)[0:4]
        versie = str(math.ceil((date.minute + (date.hour * 60)) / 5))

        input_data = InputData(
            publication_settings=dso_models.PublicationSettings(
                document_type=document_type.value.upper(),
                datum_bekendmaking=datum,
                datum_juridisch_werkend_vanaf="2024-02-28",
                provincie_id="pv28",
                wId_suffix=work_version,
                soort_bestuursorgaan="Provinciale_staten",
                expression_taal="nld",
                regeling_componentnaam="nieuweregeling",
                provincie_ref="/tooi/id/provincie/pv28",
                opdracht={
                    "opdracht_type": opdracht_type.value,
                    "id_levering": str(uuid.uuid4()),
                    "id_bevoegdgezag": "00000001002306608000",
                    "id_aanleveraar": "00000001002306608000",
                    "publicatie_bestand": f"akn_nl_bill_pv28-{datum}-{versie}.xml",
                    "datum_bekendmaking": "2024-02-28",
                },
                doel=dso_models.Doel(jaar="2024", naam=f"Instelling{document_type_title.capitalize()}"),
                besluit_frbr={
                    "work_land": "nl",
                    "work_datum": jaar,
                    "work_overig": f"{document_type.value.lower()}_{work_version}",
                    "expression_taal": "nld",
                    "expression_datum": datum,
                    "expression_versie": versie,
                    "expression_overig": None,
                },
                regeling_frbr={
                    "work_land": "nl",
                    "work_datum": jaar,
                    "work_overig": f"{document_type.value.lower()}_{work_version}",
                    "expression_taal": "nld",
                    "expression_datum": datum,
                    "expression_versie": versie,
                    "expression_overig": None,
                },
            ),
            besluit=Besluit(
                officiele_titel=f"Opschrift besluit - {document_type_title.capitalize()} {datetime.utcnow()}",
                regeling_opschrift=f"{document_type_title.capitalize()} Provincie Zuid-Holland {datetime.utcnow()}",
                aanhef=f"Om de {document_type_title.capitalize()} Provincie Zuid-Holland beschikbaar te maken in het Digitale Stelsel van de Omgevingswet is het noodzakelijk dat de reeds vastgestelde {document_type_title.capitalize()} Zuid-Holland opnieuw wordt gepubliceerd en bekend gemaakt.",
                wijzig_artikel=Artikel(
                    label="Artikel",
                    inhoud='Zoals is aangegeven in <IntRef ref="cmp_A">Bijlage A bij Artikel I</IntRef>',
                ),
                tekst_artikelen=[],
                tijd_artikel=Artikel(
                    label="Artikel",
                    inhoud="Dit besluit treedt in werking op de dag waarop dit bekend wordt gemaakt.",
                ),
                sluiting="Gegeven te 's-Gravenhage, 28 februari 2024",
                ondertekening="Gedupeerde Staten",
                rechtsgebieden=[
                    "Omgevingsrecht",
                ],
                onderwerpen=["ruimtelijke_ordening"],
                soort_procedure="Definitief_besluit",
            ),
            regeling=Regeling(
                versienummer="1",
                officiele_titel=f"{document_type_title.capitalize()} Provincie Zuid-Holland {datetime.utcnow()}",
                citeertitel=f"Citeertitel {document_type_title.lower()} hello World",
                is_officieel="true",
                rechtsgebieden=[
                    "Omgevingsrecht",
                ],
                onderwerpen=["ruimtelijke_ordening"],
            ),
            regeling_vrijetekst=free_text_template_str,
            procedure_verloop=dso_models.ProcedureVerloop(
                bekend_op="2024-02-06",
                stappen=[
                    dso_models.ProcedureStap(
                        soort_stap="Vaststelling",
                        voltooid_op="2024-01-05",
                    ),
                    dso_models.ProcedureStap(
                        soort_stap="Ondertekening",
                        voltooid_op="2024-01-06",
                    ),
                    # dso_models.ProcedureStap(
                    #     soort_stap="Publicatie",
                    #     voltooid_op="2024-02-07",
                    # ),
                ],
            ),
            resources=Resources(
                policy_object_repository=self._get_policy_object_repository(used_objects),
                asset_repository=asset_repository,
                werkingsgebied_repository=werkingsgebied_repository,
            ),
            object_template_repository=object_template_repository,
            regelingsgebied={
                "regelingsgebied": {
                    "OW_ID": "nl.imow-pv28.regelingsgebied.622f52669f684b418d484415d4ad037e",
                    "ambtsgebied": "nl.imow-pv28.ambtsgebied.002000000000000000009928",
                },
            },
        )

        return input_data

    def _get_policy_object_repository(self, used_objects: List[dict]) -> PolicyObjectRepository:
        repository = PolicyObjectRepository()
        for o in used_objects:
            repository.add(o["Code"], o)
        return repository
