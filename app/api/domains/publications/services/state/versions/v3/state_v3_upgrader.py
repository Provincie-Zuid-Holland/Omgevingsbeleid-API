import re
import uuid
from typing import Dict, Set

from lxml import etree

from app.api.domains.publications.services.state import State
from app.api.domains.publications.services.state.state_upgrader import StateUpgrader
from app.api.domains.publications.services.state.versions.v3 import models as models_v3

from ..v2 import state_v2
from ..v3 import state_v3


class StateV3Upgrader(StateUpgrader):
    @staticmethod
    def get_input_schema_version() -> int:
        return state_v2.StateV2.get_schema_version()

    def upgrade(self, environment_uuid: uuid.UUID, old_state: State) -> State:
        if old_state.get_schema_version() != state_v2.StateV2.get_schema_version():
            raise RuntimeError("Unexpected state provided")

        if not isinstance(old_state, state_v2.StateV2):
            raise RuntimeError("Unexpected state provided")

        purposes = self._mutate_purposes(old_state)
        acts = self._mutate_acts(environment_uuid, old_state)
        announcements = self._mutate_announcements(old_state)

        new_state = state_v3.StateV3(
            Purposes=purposes,
            Acts=acts,
            Announcements=announcements,
        )

        return new_state

    def _mutate_purposes(self, old_state: state_v2.StateV2) -> Dict[str, models_v3.Purpose]:
        purposes: Dict[str, models_v3.Purpose] = {}

        for key, old_purpose in old_state.Purposes.items():
            new_purpose: models_v3.Purpose = models_v3.Purpose.model_validate(old_purpose.model_dump())
            purposes[key] = new_purpose

        return purposes

    def _mutate_acts(self, environment_uuid: uuid.UUID, old_state: state_v2.StateV2) -> Dict[str, models_v3.ActiveAct]:
        acts: Dict[str, models_v3.ActiveAct] = {}

        for key, old_act in old_state.Acts.items():
            new_act: models_v3.ActiveAct = self._mutate_act(environment_uuid, old_act)
            acts[key] = new_act

        return acts

    def _mutate_act(self, environment_uuid: uuid.UUID, old_act: state_v2.models.ActiveAct) -> models_v3.ActiveAct:
        act_dict: dict = old_act.model_dump()
        act_dict["Assets"] = self._get_assets(old_act.Act_Text)

        act: models_v3.ActiveAct = models_v3.ActiveAct.model_validate(act_dict)
        return act

    def _get_assets(self, act_text: str) -> Dict[str, models_v3.Asset]:
        parser: ActTextAssetParser = ActTextAssetParser()
        asset_uuids: Set[str] = parser.get_asset_uuids(act_text)

        result: Dict[str, models_v3.Asset] = {x: models_v3.Asset(UUID=x) for x in asset_uuids}
        return result

    def _mutate_announcements(self, old_state: state_v2.StateV2) -> Dict[str, models_v3.ActiveAnnouncement]:
        announcements: Dict[str, models_v3.ActiveAnnouncement] = {}

        for key, old_announcement in old_state.Announcements.items():
            new_announcement: models_v3.ActiveAnnouncement = models_v3.ActiveAnnouncement.model_validate(
                old_announcement.model_dump()
            )
            announcements[key] = new_announcement

        return announcements


class ActTextAssetParser:
    def __init__(self):
        self._uuid_regex = r"img_([a-f0-9\-]+)\.(png|jpg|jpeg|gif|bmp|tiff|webp)"

    def get_asset_uuids(self, act_text: str) -> Set[str]:
        parser = etree.XMLParser(ns_clean=True)
        tree = etree.fromstring(act_text, parser)
        namespaces = {"ns": "https://standaarden.overheid.nl/stop/imop/tekst/"}
        illustraties = tree.xpath("//ns:Illustratie", namespaces=namespaces)

        asset_uuids: Set[str] = set()
        for illustratie in illustraties:
            uuidx = self._extract_uuid(illustratie.attrib.get("naam", ""))
            asset_uuids.add(uuidx)

        return asset_uuids

    def _extract_uuid(self, name: str) -> str:
        match = re.search(self._uuid_regex, name)
        if match:
            return match.group(1)

        raise RuntimeError("Unable to find asset uuid in the name: '{name}'")
