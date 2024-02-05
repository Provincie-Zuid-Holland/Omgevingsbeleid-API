from collections import defaultdict
from typing import List

from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from jinja2 import Template

from app.extensions.playground.templates.text_template import TextTemplate


class TemplateParser:
    def __init__(self, template_style: TextTemplate):
        self._template_style: TextTemplate = template_style

    def get_parsed_template(self, objects: List[dict]) -> str:
        aggregated_objects = defaultdict(list)
        for o in objects:
            aggregated_objects[o["Object_Type"]].append(o)

        base_template_str = self._template_style.get_free_text_template()
        base_template = Template(base_template_str)
        free_text_template_str = base_template.render(
            **aggregated_objects,
        )
        free_text_template_str = free_text_template_str.strip()
        free_text_template_str = free_text_template_str.replace("\n", "")

        return free_text_template_str

    def get_object_template_repository(self) -> ObjectTemplateRepository:
        object_templates = self._template_style.get_object_templates()
        repository = ObjectTemplateRepository(object_templates)
        return repository

    def get_object_types(self) -> List[str]:
        object_types: List[str] = self._template_style.get_object_types()
        return object_types

    def get_field_map(self) -> List[str]:
        field_map = [
            "UUID",
            "Object_Type",
            "Object_ID",
            "Code",
            "Hierarchy_Code",
            "Werkingsgebied_Code",
            "Title",
            "Description",
            "Cause",
            "Provincial_Interest",
            "Explanation",
            "Role",
            "Effect",
            # Used for Werkingsgebied
            "Area_UUID",
            "Created_Date",
            "Modified_Date",
        ]
        return field_map
