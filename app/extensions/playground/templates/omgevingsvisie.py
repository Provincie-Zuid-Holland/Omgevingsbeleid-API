from typing import Dict, List

from app.extensions.playground.templates.text_template import TextTemplate

# @note: This data will at some points be manages in the GUI


class OmgevingsvisieTextTemplate(TextTemplate):
    def get_object_types(self) -> List[str]:
        object_types = [
            "visie_algemeen",
            "ambitie",
            "beleidsdoel",
            "beleidskeuze",
            "werkingsgebied",
        ]
        return object_types

    def get_free_text_template(self) -> str:
        template = """
<div><object code="visie_algemeen-1" /></div>
<div><object code="visie_algemeen-2" /></div>
<div><object code="visie_algemeen-3" /></div>
<div><object code="visie_algemeen-4" /></div>
<div><object code="visie_algemeen-5" /></div>
<div><object code="visie_algemeen-6" /></div>
<div><object code="visie_algemeen-7" /></div>

<div>
    <h1>Ambities van Zuid-Holland</h1>
    {%- for a in ambitie | sort(attribute='Title') %}
        <div data-hint-element="divisietekst"><object code="{{ a.Code }}" template="ambitie" /></div>
    {%- endfor %}
</div>

<div>
    <h1>Beleidsdoelen en beleidskeuzes</h1>

    {%- for d in beleidsdoel | sort(attribute='Title') %}
        <div>
            <object code="{{ d.Code }}" template="beleidsdoel" />

            {% set filtered_results = beleidskeuze | selectattr('Hierarchy_Code', 'equalto', d.Code) | list %}
            {% if filtered_results %}
            <div>
                <h1>Beleidskeuzes van {{ d.Title }}</h1>
                {%- for k in filtered_results | sort(attribute='Title') %}
                <div><object code="{{ k.Code }}" template="beleidskeuze" /></div>
                {%- endfor %}
            </div>
            {% endif %}
        </div>
    {%- endfor %}
</div>

<div><object code="visie_algemeen-8" /></div>
"""
        return template

    def get_object_templates(self) -> Dict[str, str]:
        object_templates = {
            "visie_algemeen": """
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
{% if o.Werkingsgebied_Code is not none %}
<!--[GEBIED-CODE:{{o.Werkingsgebied_Code}}]-->
{% endif %}

{% if o.Description | has_text %}
    <h6>Wat wil de provincie bereiken?</h6>
    {{ o.Description }}
{% endif %}

{% if o.Cause | has_text %}
    <h6>Aanleiding</h6>
    {{ o.Cause }}
{% endif %}

{% if o.Provincial_Interest | has_text %}
    <h6>Motivering Provinciaal Belang</h6>
    {{ o.Provincial_Interest }}
{% endif %}

{% if o.Explanation | has_text %}
    <h6>Nadere uitwerking</h6>
    {{ o.Explanation }}
{% endif %}
""",
        }
        return object_templates
