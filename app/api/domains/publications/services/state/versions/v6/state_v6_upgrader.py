from uuid import UUID
from typing import Dict

from sqlalchemy.orm import Session

import app.api.domains.publications.services.state.versions.v5.models as models_v5
import app.api.domains.publications.services.state.versions.v6.models as models_v6
from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader

from ..v5 import state_v5
from ..v6 import state_v6


class StateV6Upgrader(StateUpgrader):
    """
    Patches the state for Gebieden and Gebiedengroepen system
    """

    @staticmethod
    def get_input_schema_version() -> int:
        return state_v5.StateV5.get_schema_version()

    def upgrade(self, session: Session, environment_uuid: UUID, old_state: State) -> State:
        if old_state.get_schema_version() != state_v5.StateV5.get_schema_version():
            raise RuntimeError("Unexpected state provided")

        if not isinstance(old_state, state_v5.StateV5):
            raise RuntimeError("Unexpected state provided")

        purposes = self._mutate_purposes(old_state)
        acts = self._mutate_acts(old_state)
        announcements = self._mutate_announcements(old_state)

        new_state = state_v6.StateV6(
            Purposes=purposes,
            Acts=acts,
            Announcements=announcements,
        )

        return new_state

    def _mutate_purposes(self, old_state: state_v5.StateV5) -> Dict[str, models_v6.Purpose]:
        purposes: Dict[str, models_v6.Purpose] = {}

        for key, old_purpose in old_state.Purposes.items():
            new_purpose: models_v6.Purpose = models_v6.Purpose.model_validate(old_purpose.model_dump())
            purposes[key] = new_purpose

        return purposes

    def _mutate_announcements(self, old_state: state_v5.StateV5) -> Dict[str, models_v6.ActiveAnnouncement]:
        announcements: Dict[str, models_v6.ActiveAnnouncement] = {}

        for key, old_announcement in old_state.Announcements.items():
            new_announcement: models_v6.ActiveAnnouncement = models_v6.ActiveAnnouncement.model_validate(
                old_announcement.model_dump()
            )
            announcements[key] = new_announcement

        return announcements

    def _mutate_acts(self, old_state: state_v5.StateV5) -> Dict[str, models_v6.ActiveAct]:
        acts: Dict[str, models_v6.ActiveAct] = {}

        for key, old_act in old_state.Acts.items():
            new_act: models_v6.ActiveAct = self._mutate_act(old_act)
            acts[key] = new_act

        return acts

    def _mutate_act(self, old_act: models_v5.ActiveAct) -> models_v6.ActiveAct:
        act_dict: dict = old_act.model_dump()
        resolved_gios: Dict[str, models_v6.Gio] = self._resolve_gios(old_act)
        act_dict["Gios"] = resolved_gios
        act_dict["Gebiedengroepen"] = self._resolve_gebiedengroepen(old_act)
        act_dict["Gebiedsaanwijzingen"] = {}
        # act_dict["Ow_State"] = self._resolve_ow_state(old_act)
        act_dict["Ow_State"] = models_v6.OwState.model_validate(old_act.Ow_State.model_dump())

        act: models_v6.ActiveAct = models_v6.ActiveAct.model_validate(act_dict)
        return act

    def _resolve_gios(self, old_act: models_v5.ActiveAct) -> Dict[str, models_v6.Gio]:
        result_gios: Dict[str, models_v6.Gio] = {}
        for old_werkingsgebied in old_act.Werkingsgebieden.values():
            """
            In the old werkingsgebieden system an Object Werkingsgebied
            was transformed into a dso.Werkingsgebied with 1 dso.Location
            So the Object Werkingsgebied played the role of Gebiedengroep with 1 Gebied
            """
            for index, old_location in enumerate(old_werkingsgebied.Locations):
                # We use the Werkingsgebied code with a suffix to make it unique
                # As we dont have a code, but we need one
                # This actually works fine, as this code will not exists in the next publication
                # Therefor the dso objects will be removed with the next publication
                gebied_code: str = f"werkingsgebied-{old_werkingsgebied.Object_ID}-{index + 1}"

                # Now in the new system with Gebiedsaanwijzingen, we can have an Gebiedsaanwijzing
                # to more then one Gebied. But then that whole collection must be registered as
                # a GIO.
                # If the "whole collection" of a gebiedsaanwijzing is just a Gebied that
                # we are already sending, then we would create the GIO twice which is not allowed.
                # So we have to extract the GIO from the Gebied.
                # So both the Gebied and Gebiedsaanwijzing can point to a GIO
                # And the GIO must be kept alive as long as at least one things references the GIO
                gio_locatie: models_v6.GioLocatie = models_v6.GioLocatie(
                    title=old_location.Title,
                    basisgeo_id=old_location.Identifier,
                    source_hash=old_werkingsgebied.Hash,
                    source_code=gebied_code,
                )
                gio: models_v6.Gio = models_v6.Gio(
                    geboorteregeling=old_werkingsgebied.Owner_Act,
                    achtergrond_actualiteit="",
                    achtergrond_verwijzing="",
                    frbr=models_v6.Frbr.model_validate(old_werkingsgebied.Frbr.model_dump()),
                    title=old_location.Title,
                    locaties=[gio_locatie],
                    source_codes={gebied_code},
                )
                result_gios[gio.get_code()] = gio

        return result_gios

    def _resolve_gebiedengroepen(self, old_act: models_v5.ActiveAct) -> Dict[str, models_v6.Gebiedengroep]:
        result: Dict[str, models_v6.Gebiedengroep] = {}
        for old_werkingsgebied in old_act.Werkingsgebieden.values():
            werkingsgebied_code: str = f"werkingsgebied-{old_werkingsgebied.Object_ID}"
            gebied_code: str = f"{werkingsgebied_code}-1"

            result[werkingsgebied_code] = models_v6.Gebiedengroep(
                uuid=old_werkingsgebied.UUID,
                code=werkingsgebied_code,
                object_id=-1,
                title=old_werkingsgebied.Title,
                gio_keys=set([gebied_code]),
            )

        return result
