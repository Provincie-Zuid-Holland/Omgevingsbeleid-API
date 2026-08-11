from collections import defaultdict

from jinja2 import Template


class TemplateParser:
    def get_parsed_template(self, text_template: str, objects: list[dict]) -> str:
        aggregated_objects = defaultdict(list)
        for o in objects:
            aggregated_objects[o["Object_Type"]].append(o)

        base_template = Template(text_template)
        free_text_template_str = base_template.render(
            **aggregated_objects,
        )
        free_text_template_str = free_text_template_str.strip()
        free_text_template_str = free_text_template_str.replace("\n", "")

        return free_text_template_str
