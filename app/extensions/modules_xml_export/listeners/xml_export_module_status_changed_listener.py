from typing import List, Optional
from fastapi import BackgroundTasks
import xml.dom.minidom as minidom

from fs.osfs import OSFS
from dicttoxml import dicttoxml
from app.dynamic.converter import Converter

from app.dynamic.event.types import Listener
from app.extensions.modules.event.module_status_changed_event import (
    ModuleStatusChangedEvent,
)
from app.extensions.modules.models.models import ModuleSnapshot


class XMLExportModuleStatusChangedListener(Listener[ModuleStatusChangedEvent]):
    def __init__(self, converter: Converter, main_config: dict):
        self._converter: Converter = converter
        self._destination_path_prefix: Optional[str] = None

        config_dict: dict = main_config.get("modules_xml_export")
        destination_path_prefix: str = (
            f"./output/{config_dict.get('destination_path')}"
        ).replace("//", "/")
        self._destination_path_prefix = destination_path_prefix

    def handle_event(self, event: ModuleStatusChangedEvent) -> ModuleStatusChangedEvent:
        if not self._destination_path_prefix:
            return None

        destination_dir: str = "/".join(
            [
                self._destination_path_prefix,
                f"module-{event.context.module.Module_ID}",
                f"{str(event.context.new_status.Created_Date).replace(' ', '_')}-{event.context.new_status.Status}",
            ]
        )
        destination_dir = destination_dir.replace("//", "/")
        snapshot: ModuleSnapshot = event.get_snapshot()

        object_dicts: List[dict] = []
        for obj in snapshot.Objects:
            object_dicts.append(self._converter.serialize(obj.get("Object_Type"), obj))

        task_runner: BackgroundTasks = event.get_task_runner()
        task_runner.add_task(_create_xmls, destination_dir, object_dicts)


def _create_xmls(
    destination_dir: str,
    object_dicts: List[dict],
):
    with OSFS(".") as destination_fs:
        with destination_fs.makedirs(
            destination_dir, recreate=True
        ) as destination_dir_fs:
            xml_content = dicttoxml(object_dicts, attr_type=False)
            filename: str = "objects.xml"
            destination_dir_fs.appendbytes(filename, xml_content)

            dom = minidom.parseString(xml_content)
            pretty_xml_as_string = dom.toprettyxml()
            filename = "objects-pretty.xml"
            destination_dir_fs.appendtext(filename, pretty_xml_as_string)
