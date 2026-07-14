from datetime import datetime, timezone

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.publications.publication_template_spec import PublicationTemplateSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Created_Date=datetime(2025, 9, 1, tzinfo=timezone.utc),
        Modified_Date=datetime(2025, 9, 1, tzinfo=timezone.utc),
        Created_By_UUID=col.ref(UserSpec, "admin"),
        Modified_By_UUID=col.ref(UserSpec, "admin"),
    ):
        col.add(
            PublicationTemplateSpec(
                key="omgevingsvisie-simple",
                Title="Template Omgevingsvisie Module 1",
                Description="Description for Template Omgevingsvisie Module 1",
                Is_Active=True,
                Document_Type="omgevingsvisie",
                Object_Types=[
                    "beleidsdoel",
                    "beleidskeuze",
                ],
                Text_Template="""
<div data-hint-element="divisietekst"><object code="beleidsdoel-1" /></div>
<div data-hint-element="divisietekst"><object code="beleidskeuze-1" /></div>
""",
                Object_Templates={
                    "beleidsdoel": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE: {{ o.Code }}]-->
{{ o.Description | default('', true)}}
""",
                    "beleidskeuze": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE: {{ o.Code }}]-->
{{ o.Description | default('', true)}}

<h5>Toelichting</h5>
{{ o.Explanation | default('', true)}}
""",
                },
                Object_Field_Map={
                    "beleidsdoel": ["Title", "Description"],
                    "beleidskeuze": ["Title", "Description", "Explanation", "Gebiedengroep_Code"],
                },
            )
        )

        col.add(
            PublicationTemplateSpec(
                key="programma-simple",
                Title="Template Programma Module 1",
                Description="Description for Template Programma Module 1",
                Is_Active=True,
                Document_Type="programma",
                Object_Types=[
                    "beleidskeuze",
                    "maatregel",
                ],
                Text_Template="""
<div data-hint-element="divisietekst"><object code="beleidskeuze-1" /></div>
<div data-hint-element="divisietekst"><object code="maatregel-1" /></div>
""",
                Object_Templates={
                    "beleidskeuze": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE: {{ o.Code }}]-->
{{ o.Description | default('', true)}}
""",
                    "maatregel": """
<h1>{{ o.Title }}</h1>
<!--[OBJECT-CODE: {{ o.Code }}]-->
{{ o.Description | default('', true)}}

<h5>Uitwerking</h5>
{{ o.Effect | default('', true)}}
""",
                },
                Object_Field_Map={
                    "beleidskeuze": ["Title", "Description", "Gebiedengroep_Code"],
                    "maatregel": ["Title", "Description", "Effect"],
                },
            )
        )
