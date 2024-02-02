from typing import Dict, List

from app.extensions.playground.templates.text_template import TextTemplate

# @note: This data will at some points be manages in the GUI


class ProgrammaTextTemplate(TextTemplate):
    def get_object_types(self) -> List[str]:
        object_types = [
            "programma_algemeen",
            "beleidsdoel",
            "beleidskeuze",
            "maatregel",
            "werkingsgebied",
        ]
        return object_types

    def get_free_text_template(self) -> str:
        template = """
{%- for d in beleidsdoel | sort(attribute='Title') %}
    <div>
        <object code="{{ d.Code }}" template="beleidsdoel" />

        {% set beleidskeuzes_codes_for_beleidsdoel = beleidskeuze | selectattr('Hierarchy_Code', 'equalto', d.Code) | map(attribute='Code') | list %}

        {% set maatregelen_for_doel = maatregel | selectattr('Hierarchy_Code', 'in', beleidskeuzes_codes_for_beleidsdoel) | list %}
        {% if maatregelen_for_doel %}
        <div>
            <h1>Maatregelen van {{ d.Title }}</h1>
            {%- for m in maatregelen_for_doel | sort(attribute='Title') %}
            <div><object code="{{ m.Code }}" template="maatregel" /></div>
            {%- endfor %}
        </div>
        {% endif %}
    </div>
{%- endfor %}

"""
        return template

    def get_object_templates(self) -> Dict[str, str]:
        object_templates = {
            "programma_algemeen": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description | default('', true) }}
""",
            "beleidsdoel": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description | default('', true) }}
""",
            "maatregel": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{% if o.Gebied_UUID is not none %}
<!--[GEBIED-UUID:{{o.Gebied_UUID}}]-->
{% endif %}

{% if o.Description %}
<h2>Wat wil de provincie bereiken?</h2>
{{ o.Description }}
{% endif %}

{% if o.Role %}
<h2>Rolkeuze</h2>
{{ o.Role }}
{% endif %}

{% if o.Effect %}
<h2>Uitwerking</h2>
{{ o.Effect }}
{% endif %}
""",
        }
        return object_templates
