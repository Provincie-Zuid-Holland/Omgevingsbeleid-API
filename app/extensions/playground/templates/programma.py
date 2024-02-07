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
            <div data-hint-element="divisietekst"><object code="{{ m.Code }}" template="maatregel" /></div>
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
{% if o.Werkingsgebied_Code is not none %}
<!--[GEBIED-CODE:{{o.Werkingsgebied_Code}}]-->
{% endif %}

{% if o.Description | has_text %}
    <h6>Wat wil de provincie bereiken?</h6>
    {{ o.Description }}
{% endif %}

{% if o.Role | has_text %}
    <h6>Rolkeuze</h6>
    <p>{{ o.Role }}</p>
{% endif %}

{% if o.Effect | has_text  %}
    <h6>Uitwerking</h6>
    {{ o.Effect }}
{% endif %}

""",
        }
        return object_templates
