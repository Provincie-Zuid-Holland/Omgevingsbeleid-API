import uuid
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


class InputDataService:
    def create(
        self,
        used_objects: List[dict],
        free_text_template_str: str,
        object_template_repository: ObjectTemplateRepository,
        asset_repository: DSOAssetRepository,
        werkingsgebied_repository: WerkingsgebiedRepository,
    ) -> InputData:
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
                    "id_levering": str(uuid.uuid4()),
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
            regeling_vrijetekst=free_text_template_str,
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
                policy_object_repository=self._get_policy_object_repository(used_objects),
                asset_repository=asset_repository,
                werkingsgebied_repository=werkingsgebied_repository,
            ),
            object_template_repository=object_template_repository,
        )

        return input_data

    def _get_policy_object_repository(self, used_objects: List[dict]) -> PolicyObjectRepository:
        repository = PolicyObjectRepository()
        for o in used_objects:
            repository.add(o["Code"], o)
        return repository
