import uuid
from typing import Dict

from sqlalchemy.orm import Session

import app.api.domains.publications.services.state.versions.v3.models as models_v3
import app.api.domains.publications.services.state.versions.v4.models as models_v4
from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader

from ..v3 import state_v3
from ..v4 import state_v4


class StateV4Upgrader(StateUpgrader):
    @staticmethod
    def get_input_schema_version() -> int:
        return state_v3.StateV3.get_schema_version()

    def upgrade(self, session: Session, environment_uuid: uuid.UUID, old_state: State) -> State:
        if old_state.get_schema_version() != state_v3.StateV3.get_schema_version():
            raise RuntimeError("Unexpected state provided")

        if not isinstance(old_state, state_v3.StateV3):
            raise RuntimeError("Unexpected state provided")

        purposes = self._mutate_purposes(old_state)
        acts = self._mutate_acts(environment_uuid, old_state)
        announcements = self._mutate_announcements(old_state)

        new_state = state_v4.StateV4(
            Purposes=purposes,
            Acts=acts,
            Announcements=announcements,
        )

        return new_state

    def _mutate_purposes(self, old_state: state_v3.StateV3) -> Dict[str, models_v4.Purpose]:
        purposes: Dict[str, models_v4.Purpose] = {}

        for key, old_purpose in old_state.Purposes.items():
            new_purpose: models_v4.Purpose = models_v4.Purpose.model_validate(old_purpose.model_dump())
            purposes[key] = new_purpose

        return purposes

    def _mutate_acts(self, environment_uuid: uuid.UUID, old_state: state_v3.StateV3) -> Dict[str, models_v4.ActiveAct]:
        acts: Dict[str, models_v4.ActiveAct] = {}

        for key, old_act in old_state.Acts.items():
            new_act: models_v4.ActiveAct = self._mutate_act(environment_uuid, old_act)
            acts[key] = new_act

        return acts

    def _mutate_act(self, environment_uuid: uuid.UUID, old_act: state_v3.models.ActiveAct) -> models_v4.ActiveAct:
        act_dict: dict = old_act.model_dump()
        act_dict["Werkingsgebieden"] = self._resolve_werkingsgebieden(old_act.Werkingsgebieden)

        act: models_v4.ActiveAct = models_v4.ActiveAct.model_validate(act_dict)
        return act

    def _resolve_werkingsgebieden(
        self, old_werkingsgebieden: Dict[int, models_v3.Werkingsgebied]
    ) -> Dict[int, models_v4.Werkingsgebied]:
        result: Dict[int, models_v4.Werkingsgebied] = {}

        for object_id, old_werkingsgebied in old_werkingsgebieden.items():
            # The old style have one location which is itself
            # And the ids are based on its uuid
            # We mimic this old behaviour as result
            act_id: str = old_werkingsgebied.Frbr.Work_Other.split("-")[0]
            base_id: str = f"lo-{act_id}-{old_werkingsgebied.UUID}"

            location = models_v4.Location(
                UUID=old_werkingsgebied.UUID,
                Identifier=base_id,
                Gml_ID=f"gml-{base_id}",
                Group_ID=f"groep-{base_id}",
                Title=old_werkingsgebied.Title,
            )
            result[object_id] = models_v4.Werkingsgebied(
                UUID=old_werkingsgebied.UUID,
                Identifier=old_werkingsgebied.Identifier,
                Hash=old_werkingsgebied.Hash,
                Object_ID=old_werkingsgebied.Object_ID,
                Title=old_werkingsgebied.Title,
                Owner_Act=old_werkingsgebied.Owner_Act,
                Frbr=models_v4.Frbr.model_validate(old_werkingsgebied.Frbr.model_dump()),
                Locations=[location],
            )

        return result

    def _mutate_announcements(self, old_state: state_v3.StateV3) -> Dict[str, models_v4.ActiveAnnouncement]:
        announcements: Dict[str, models_v4.ActiveAnnouncement] = {}

        for key, old_announcement in old_state.Announcements.items():
            new_announcement: models_v4.ActiveAnnouncement = models_v4.ActiveAnnouncement.model_validate(
                old_announcement.model_dump()
            )
            announcements[key] = new_announcement

        return announcements
