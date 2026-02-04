import uuid
from typing import Dict, List, Set

from sqlalchemy.orm import Session

import app.api.domains.publications.services.state.versions.v4.models as models_v4
import app.api.domains.publications.services.state.versions.v5.models as models_v5
from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader

from ..v4 import state_v4
from ..v5 import state_v5


class StateV5Upgrader(StateUpgrader):
    """
    Patches the state for the new OWState system
    """

    @staticmethod
    def get_input_schema_version() -> int:
        return state_v4.StateV4.get_schema_version()

    def upgrade(self, session: Session, environment_uuid: uuid.UUID, old_state: State) -> State:
        if old_state.get_schema_version() != state_v4.StateV4.get_schema_version():
            raise RuntimeError("Unexpected state provided")

        if not isinstance(old_state, state_v4.StateV4):
            raise RuntimeError("Unexpected state provided")

        purposes = self._mutate_purposes(old_state)
        acts = self._mutate_acts(old_state)
        announcements = self._mutate_announcements(old_state)

        new_state = state_v5.StateV5(
            Purposes=purposes,
            Acts=acts,
            Announcements=announcements,
        )

        return new_state

    def _mutate_purposes(self, old_state: state_v4.StateV4) -> Dict[str, models_v5.Purpose]:
        purposes: Dict[str, models_v5.Purpose] = {}

        for key, old_purpose in old_state.Purposes.items():
            new_purpose: models_v5.Purpose = models_v5.Purpose.model_validate(old_purpose.model_dump())
            purposes[key] = new_purpose

        return purposes

    def _mutate_announcements(self, old_state: state_v4.StateV4) -> Dict[str, models_v5.ActiveAnnouncement]:
        announcements: Dict[str, models_v5.ActiveAnnouncement] = {}

        for key, old_announcement in old_state.Announcements.items():
            new_announcement: models_v5.ActiveAnnouncement = models_v5.ActiveAnnouncement.model_validate(
                old_announcement.model_dump()
            )
            announcements[key] = new_announcement

        return announcements

    def _mutate_acts(self, old_state: state_v4.StateV4) -> Dict[str, models_v5.ActiveAct]:
        acts: Dict[str, models_v5.ActiveAct] = {}

        for key, old_act in old_state.Acts.items():
            new_act: models_v5.ActiveAct = self._mutate_act(old_act)
            acts[key] = new_act

        return acts

    def _mutate_act(self, old_act: models_v4.ActiveAct) -> models_v5.ActiveAct:
        act_dict: dict = old_act.model_dump()
        act_dict["Ow_State"] = self._resolve_ow_state(old_act)

        act: models_v5.ActiveAct = models_v5.ActiveAct.model_validate(act_dict)
        return act

    def _resolve_ow_state(self, old_act: models_v4.ActiveAct) -> models_v5.OwState:
        ambtsgebieden: Set[models_v5.OwAmbtsgebied] = set()
        regelingsgebieden: Set[models_v5.OwRegelingsgebied] = set()
        gebieden: Set[models_v5.OwGebied] = set()
        gebiedengroepen: Set[models_v5.OwGebiedengroep] = set()
        gebiedsaanwijzingen: Set[models_v5.OwGebiedsaanwijzing] = set()
        divisies: Set[models_v5.OwDivisie] = set()
        divisieteksten: Set[models_v5.OwDivisietekst] = set()
        tekstdelen: Set[models_v5.OwTekstdeel] = set()

        ow_objects = old_act.Ow_Data.Ow_Objects
        for ow_id, ow_object in ow_objects.items():
            ow_type: str = ow_object.get("ow_type", "")
            match ow_type:
                case "OWAmbtsgebied":
                    ambtsgebieden.add(
                        models_v5.OwAmbtsgebied(
                            object_status=models_v5.OwObjectStatus.unchanged,
                            identification=ow_object["OW_ID"],
                            procedure_status=ow_object["procedure_status"],
                            source_uuid=ow_object["mapped_uuid"],
                            administrative_borders_id=ow_object["bestuurlijke_grenzen_verwijzing"][
                                "bestuurlijke_grenzen_id"
                            ],
                            domain=ow_object["bestuurlijke_grenzen_verwijzing"]["domein"],
                            valid_on=ow_object["bestuurlijke_grenzen_verwijzing"]["geldig_op"],
                            title="",
                        )
                    )
                case "OWRegelingsgebied":
                    locatie_ref = models_v5.AmbtsgebiedRef(ref=ow_object["ambtsgebied"])
                    regelingsgebieden.add(
                        models_v5.OwRegelingsgebied(
                            object_status=models_v5.OwObjectStatus.unchanged,
                            identification=ow_object["OW_ID"],
                            procedure_status=ow_object["procedure_status"],
                            source_uuid=ow_objects[ow_object["ambtsgebied"]]["mapped_uuid"],
                            locatie_ref=locatie_ref,
                        )
                    )
                case "OWGebied":
                    gio_ref = ow_object.get("gio_ref") or ow_object.get("mapped_uuid")
                    gebieden.add(
                        models_v5.OwGebied(
                            object_status=models_v5.OwObjectStatus.unchanged,
                            identification=ow_object["OW_ID"],
                            procedure_status=ow_object["procedure_status"],
                            source_uuid=gio_ref,
                            source_code=f"{ow_object['mapped_geo_code']}-0",
                            title=ow_object["noemer"],
                            geometry_ref=gio_ref,
                        )
                    )
                case "OWGebiedenGroep":
                    gio_ref = ow_object.get("gio_ref") or ow_object.get("mapped_uuid")
                    gebieden_ref = models_v5.GebiedRef(
                        target_code=f"{ow_object['mapped_geo_code']}-0",
                        ref=ow_object["gebieden"][0],
                    )
                    gebiedengroepen.add(
                        models_v5.OwGebiedengroep(
                            object_status=models_v5.OwObjectStatus.unchanged,
                            identification=ow_object["OW_ID"],
                            procedure_status=ow_object["procedure_status"],
                            source_uuid=gio_ref,
                            source_code=ow_object["mapped_geo_code"],
                            title=ow_object["noemer"],
                            gebieden_refs=[gebieden_ref],
                        )
                    )
                case "OWDivisieTekst":
                    divisieteksten.add(
                        models_v5.OwDivisietekst(
                            object_status=models_v5.OwObjectStatus.unchanged,
                            identification=ow_object["OW_ID"],
                            procedure_status=ow_object["procedure_status"],
                            source_uuid="",
                            source_code=ow_object["mapped_policy_object_code"],
                            wid=ow_object["wid"],
                        )
                    )
                case "OWTekstdeel":
                    text_ref = models_v5.DivisietekstRef(
                        target_wid=ow_objects[ow_object["divisie"]]["wid"],
                        ref=ow_object["divisie"],
                    )
                    try:
                        location_refs: List[models_v5.LocationRefUnion] = []
                        for l_ref in ow_object["locaties"]:
                            if "ambtsgebied" in l_ref:
                                location_refs.append(
                                    models_v5.AmbtsgebiedRef(
                                        ref=l_ref,
                                    )
                                )
                            else:
                                location_refs.append(
                                    models_v5.GebiedengroepRef(
                                        target_code=ow_objects[l_ref]["mapped_geo_code"],
                                        ref=l_ref,
                                    )
                                )

                    except Exception as e:
                        raise e
                    tekstdelen.add(
                        models_v5.OwTekstdeel(
                            object_status=models_v5.OwObjectStatus.unchanged,
                            identification=ow_object["OW_ID"],
                            procedure_status=ow_object["procedure_status"],
                            source_uuid="",
                            source_code=ow_objects[ow_object["divisie"]]["mapped_policy_object_code"],
                            idealization="http://standaarden.omgevingswet.overheid.nl/idealisatie/id/concept/Indicatief",
                            text_ref=text_ref,
                            location_refs=location_refs,
                        )
                    )
                case _:
                    # Invalid Ow State, if its a draft than we can get away with it
                    # because we dont mutate drafts
                    if old_act.Procedure_Type == "draft":
                        return models_v5.OwState()

                    raise RuntimeError(f"Unknown `ow_type` '{ow_type}'")

        result = models_v5.OwState(
            ambtsgebieden=list(ambtsgebieden),
            regelingsgebieden=list(regelingsgebieden),
            gebieden=list(gebieden),
            gebiedengroepen=list(gebiedengroepen),
            gebiedsaanwijzingen=list(gebiedsaanwijzingen),
            divisies=list(divisies),
            divisieteksten=list(divisieteksten),
            tekstdelen=list(tekstdelen),
        )
        return result
