from typing import Dict

from app.extensions.playground.templates.text_template import TextTemplate

# @note: This data will at some points be manages in the GUI


class OmgevingsprogrammaTextTemplate(TextTemplate):
    def get_free_text_template(self) -> str:
        template = """
"""
        return template

    def get_object_templates(self) -> Dict[str, str]:
        object_templates = {
            "programma_algemeen": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description | default('', true) }}
""",
            "ambitie": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description | default('', true) }}
""",
            "beleidsdoel": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description | default('', true) }}
""",
            "beleidskeuze": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{% if o.Gebied_UUID is not none %}
<!--[GEBIED-UUID:{{o.Gebied_UUID}}]-->
{% endif %}

{% if o.Description %}
<h2>Wat wil de provincie bereiken?</h2>
{{ o.Description }}
{% endif %}

{% if o.Cause %}
<h2>Aanleiding</h2>
{{ o.Cause }}
{% endif %}

{% if o.Provincial_Interest %}
<h2>Motivering Provinciaal Belang</h2>
{{ o.Provincial_Interest }}
{% endif %}

{% if o.Explanation %}
<h2>Nadere uitwerking</h2>
{{ o.Explanation }}
{% endif %}
""",
        }
        return object_templates
