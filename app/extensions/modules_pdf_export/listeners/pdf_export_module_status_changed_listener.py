from dataclasses import dataclass
from typing import Dict, Optional
from fastapi import BackgroundTasks

import jinja2
import pdfkit
from fs.osfs import OSFS

from app.dynamic.event.types import Listener
from app.extensions.modules.event.module_status_changed_event import (
    ModuleStatusChangedEvent,
)
from app.extensions.modules.models.models import ModuleSnapshot


@dataclass
class PdfExportTemplates:
    destination_path_prefix: str
    templates: Dict[str, jinja2.Template]

    @staticmethod
    def load_from_main_config(main_config: dict) -> Optional["PdfExportTemplates"]:
        if not "modules_pdf_export" in main_config:
            return None

        config_dict: dict = main_config.get("modules_pdf_export")
        destination_path_prefix: str = (
            f"./output/{config_dict.get('destination_path')}"
        ).replace("//", "/")
        template_path: str = (f"./config/{config_dict.get('template_path')}").replace(
            "//", "/"
        )

        template_loader: jinja2.FileSystemLoader = jinja2.FileSystemLoader(
            searchpath=template_path
        )
        template_env: jinja2.Environment = jinja2.Environment(loader=template_loader)

        templates: Dict[str, jinja2.Template] = {}
        for object_type, filename in config_dict.get("templates", {}).items():
            template: jinja2.Template = template_env.get_template(filename)
            templates[object_type] = template

        return PdfExportTemplates(
            destination_path_prefix=destination_path_prefix,
            templates=templates,
        )


class PdfExportModuleStatusChangedListener(Listener[ModuleStatusChangedEvent]):
    def __init__(self, main_config: dict):
        self._config: Optional[
            PdfExportTemplates
        ] = PdfExportTemplates.load_from_main_config(main_config)

    def handle_event(self, event: ModuleStatusChangedEvent) -> ModuleStatusChangedEvent:
        if not self._config:
            return None

        destination_dir: str = "/".join(
            [
                self._config.destination_path_prefix,
                f"module-{event.context.module.Module_ID}",
                f"{str(event.context.new_status.Created_Date).replace(' ', '_')}-{event.context.new_status.Status}",
            ]
        )
        destination_dir = destination_dir.replace("//", "/")
        snapshot: ModuleSnapshot = event.get_snapshot()

        task_runner: BackgroundTasks = event.get_task_runner()
        task_runner.add_task(_create_pdfs, destination_dir, snapshot, self._config)


def _create_pdfs(
    destination_dir: str,
    snapshot: ModuleSnapshot,
    config: PdfExportTemplates,
):
    with OSFS(".") as destination_fs:
        with destination_fs.makedirs(
            destination_dir, recreate=True
        ) as destination_dir_fs:
            for object in snapshot.Objects:
                object_type: str = object.get("Object_Type")
                object_id: str = object.get("Object_ID")

                if not object_type in config.templates:
                    continue

                template: jinja2.Template = config.templates.get(object_type)
                html = template.render(object=object)

                filename: str = f"{object_type}-{object_id}.pdf"
                pdf_content = pdfkit.from_string(html)
                destination_dir_fs.writebytes(filename, pdf_content)
