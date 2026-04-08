from uuid import UUID
from typing import Dict

from sqlalchemy.orm import Session

import app.api.domains.publications.services.state.versions.v6.models as models_v6
import app.api.domains.publications.services.state.versions.v7.models as models_v7
from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader

from ..v6 import state_v6
from ..v7 import state_v7


class StateV7Upgrader(StateUpgrader):
    """
    Patches that gebiedengroep targets to one GIO
        Same for gebiedsaanwijzing

    Previously it was 1 GIO per Gebied, but it needs to be a GIO per "thing" we reference in the text
    And we reference to Gebiedengroep, therefor a Gebiedengroep must be one GIO
    """

    @staticmethod
    def get_input_schema_version() -> int:
        return state_v6.StateV6.get_schema_version()

    def upgrade(self, session: Session, environment_uuid: UUID, old_state: State) -> State:
        if old_state.get_schema_version() != state_v6.StateV6.get_schema_version():
            raise RuntimeError("Unexpected state provided")

        if not isinstance(old_state, state_v6.StateV6):
            raise RuntimeError("Unexpected state provided")

        purposes = self._mutate_purposes(old_state)
        acts = self._mutate_acts(old_state)
        announcements = self._mutate_announcements(old_state)

        new_state = state_v7.StateV7(
            Purposes=purposes,
            Acts=acts,
            Announcements=announcements,
        )

        return new_state

    def _mutate_purposes(self, old_state: state_v6.StateV6) -> Dict[str, models_v7.Purpose]:
        purposes: Dict[str, models_v7.Purpose] = {}

        for key, old_purpose in old_state.Purposes.items():
            new_purpose: models_v7.Purpose = models_v7.Purpose.model_validate(old_purpose.model_dump())
            purposes[key] = new_purpose

        return purposes

    def _mutate_announcements(self, old_state: state_v6.StateV6) -> Dict[str, models_v7.ActiveAnnouncement]:
        announcements: Dict[str, models_v7.ActiveAnnouncement] = {}

        for key, old_announcement in old_state.Announcements.items():
            new_announcement: models_v7.ActiveAnnouncement = models_v7.ActiveAnnouncement.model_validate(
                old_announcement.model_dump()
            )
            announcements[key] = new_announcement

        return announcements

    def _mutate_acts(self, old_state: state_v6.StateV6) -> Dict[str, models_v7.ActiveAct]:
        acts: Dict[str, models_v7.ActiveAct] = {}

        for key, old_act in old_state.Acts.items():
            new_act: models_v7.ActiveAct = self._mutate_act(old_act)
            acts[key] = new_act

        return acts

    def _mutate_act(self, old_act: models_v6.ActiveAct) -> models_v7.ActiveAct:
        act_dict: dict = old_act.model_dump()
        resolved_gios: Dict[str, models_v7.Gio] = self._resolve_gios(old_act)
        act_dict["Gios"] = resolved_gios

        # By removing these, their references get removed and the GIOs become invalid
        act_dict["Gebiedengroepen"] = {}
        act_dict["Gebiedsaanwijzingen"] = {}

        act_dict["Ow_State"] = models_v7.OwState.model_validate(old_act.Ow_State.model_dump())

        act: models_v7.ActiveAct = models_v7.ActiveAct.model_validate(act_dict)
        return act

    def _resolve_gios(self, old_act: models_v6.ActiveAct) -> Dict[str, models_v7.Gio]:
        result_gios: Dict[str, models_v7.Gio] = {}

        # We do not bother keeping the lineage of these old GIO's alive as their origin is no longer relevant
        # Therefor all references to these gios will be made invalid (by just removing the gebiedengroepen and gebiedsaanwijzingen)
        #
        # We need to drag along all the GIO's as they need to be removed officially in the DSO system
        for old_gio_key, old_gio in old_act.Gios.items():
            new_gio = models_v7.Gio(
                key=f"invalid:{old_gio_key}",
                source_codes=old_gio.source_codes,
                title=old_gio.title,
                frbr=models_v7.Frbr.model_validate(old_gio.frbr.model_dump()),
                geboorteregeling=old_gio.geboorteregeling,
                achtergrond_verwijzing=old_gio.achtergrond_verwijzing,
                achtergrond_actualiteit=old_gio.achtergrond_actualiteit,
                locaties=[
                    models_v7.GioLocatie.model_validate(old_location.model_dump()) for old_location in old_gio.locaties
                ],
            )
            result_gios[new_gio.key] = new_gio

        return result_gios
