from jinja2 import Template

"""
Store templates in db?
"""

object_templates = {
    "visie_algemeen": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description }}
""",
    "ambitie": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE:{{o.Code}}]-->
{{ o.Description }}
""",
}

jinja_template = """

<div><object code="visie_algemeen-1" /></div>
<div><object code="visie_algemeen-2" /></div>

<div>
    <div>
        <object code="visie_algemeen-3" />
    </div>
    <div>
        <h1>Ambities van Zuid-Holland</h1>
        {%- for a in ambitie | sort(attribute='Title') %}
            <div>
                <object code="{{ a.Code }}" template="ambitie" />
            </div>
        {%- endfor %}
    </div>
</div>

<div>
    <h1>Beleidsdoelen en beleidskeuzes</h1>

</div>

"""


def create_vrijetekst_template() -> Template:
    base_template = Template(jinja_template)
    return base_template

