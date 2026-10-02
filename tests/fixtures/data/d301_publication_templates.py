from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.publications.publication_template_spec import PublicationTemplateSpec
from tests.fixtures.internal.spec.user_spec import UserSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        created_by_id=col.ref(UserSpec, "beheerder"),
        modified_by_id=col.ref(UserSpec, "beheerder"),
    ):
        col.adds(
            [
                PublicationTemplateSpec(
                    key="publication-template-programma-1",
                    title="Programma Versie 2025.01",
                    description="Programma template description",
                    is_active=False,
                    document_type="programma",
                    object_types=[],
                    text_template="",
                    object_templates={},
                    object_field_map={},
                    created_date=datetime(2025, 1, 1, tzinfo=UTC),
                    modified_date=datetime(2025, 1, 1, tzinfo=UTC),
                ),
                PublicationTemplateSpec(
                    key="publication-template-programma-2",
                    title="Programma Versie 2025.02",
                    description="Programma template description",
                    is_active=True,
                    document_type="programma",
                    object_types=["programma_algemeen", "beleidsdoel"],
                    text_template="""<div data-hint-element="divisietekst"><object code="programma_algemeen-1" /></div>""",
                    object_templates={
                        "programma_algemeen": """<h1>{{ o.Title }}</h1>\n<!--[OBJECT-CODE:{{o.Code}}]-->\n{{ o.Description | default('', true) }}""",
                        "beleidsdoel": """<h1>{{ o.Title }}</h1>\n<!--[OBJECT-CODE:{{o.Code}}]-->\n{{ o.Description | default('', true) }}""",
                    },
                    object_field_map={
                        "programma_algemeen": ["title", "description"],
                        "beleidsdoel": ["title", "description"],
                    },
                    created_date=datetime(2025, 2, 1, tzinfo=UTC),
                    modified_date=datetime(2025, 2, 1, tzinfo=UTC),
                ),
                PublicationTemplateSpec(
                    key="publication-template-visie-1",
                    title="Omgevingsvisie Versie 2025.01",
                    description="Omgevingsvisie template description",
                    is_active=False,
                    document_type="omgevingsvisie",
                    object_types=[],
                    text_template="",
                    object_templates={},
                    object_field_map={},
                    created_date=datetime(2025, 1, 2, tzinfo=UTC),
                    modified_date=datetime(2025, 1, 2, tzinfo=UTC),
                ),
                PublicationTemplateSpec(
                    key="publication-template-visie-2",
                    title="Omgevingsvisie Versie 2025.02",
                    description="Omgevingsvisie template description",
                    is_active=True,
                    document_type="omgevingsvisie",
                    object_types=["visie_algemeen", "ambitie"],
                    text_template="""<div data-hint-element="divisietekst"><object code="visie_algemeen-1" /></div>""",
                    object_templates={
                        "visie_algemeen": """<h1>{{ o.title }}</h1>\n<!--[OBJECT-CODE:{{o.code}}]-->\n{{ o.description | default('', true) }}""",
                        "ambitie": """<h1>Ambitie {{ o.title }}</h1>\n<!--[OBJECT-CODE:{{o.code}}]-->\n{{ o.description | default('', true) }}""",
                    },
                    object_field_map={
                        "visie_algemeen": ["title", "description"],
                        "ambitie": ["title", "description"],
                    },
                    created_date=datetime(2025, 2, 2, tzinfo=UTC),
                    modified_date=datetime(2025, 2, 2, tzinfo=UTC),
                ),
            ],
        )
