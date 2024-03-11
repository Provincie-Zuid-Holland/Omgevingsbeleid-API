import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.extensions.areas.db.tables import AreasTable  # # noqa
from app.extensions.publications.enums import DocumentType, ProcedureType
from app.extensions.publications.models import ActMetadata, BillCompact, BillMetadata, Procedural
from app.extensions.publications.tables.tables import (
    PublicationAreaOfJurisdictionTable,
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationTemplateTable,
    PublicationVersionTable,
)
from app.extensions.publications.waardelijsten import Onderwerp, Rechtsgebied


class DatabaseFixturesPublications:
    def __init__(self, db: Session):
        self._db = db
        self._timepoint: datetime = datetime.utcnow()
        self._user: uuid.UUID = uuid.UUID("11111111-0000-0000-0000-000000000001")

    def create_all(self):
        self.create_templates()
        self.create_environments()
        self.create_area_of_jurisdictions()
        self.create_publication()
        self.create_publication_version()

    def create_templates(self):
        # Omgevingsvisie
        self._db.add(
            PublicationTemplateTable(
                UUID=uuid.UUID("90000001-0000-0000-0000-000000000001"),
                Title="Omgevingsvisie WWW",
                Description="",
                Is_Active=True,
                Document_Type=DocumentType.VISION.value,
                Object_Types=[
                    "visie_algemeen",
                    "ambitie",
                    "beleidsdoel",
                    "beleidskeuze",
                    "werkingsgebied",
                ],
                Field_Map=[
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
                    "Area_UUID",
                    "Created_Date",
                    "Modified_Date",
                ],
                Text_Template="""
<div><object code="visie_algemeen-1" /></div>

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
                <div data-hint-element="divisietekst"><object code="{{ k.Code }}" template="beleidskeuze" /></div>
                {%- endfor %}
            </div>
            {% endif %}
        </div>
    {%- endfor %}
</div>

<div><object code="visie_algemeen-2" /></div>
""".strip(),
                Object_Templates={
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
                },
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        # Programma
        self._db.add(
            PublicationTemplateTable(
                UUID=uuid.UUID("90000001-0000-0000-0000-000000000002"),
                Title="Programma WWW",
                Description="",
                Is_Active=True,
                Document_Type=DocumentType.PROGRAM.value,
                Object_Types=[
                    "programma_algemeen",
                    "beleidsdoel",
                    "beleidskeuze",
                    "maatregel",
                    "werkingsgebied",
                ],
                Field_Map=[
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
                    "Area_UUID",
                    "Created_Date",
                    "Modified_Date",
                ],
                Text_Template="""
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
""".strip(),
                Object_Templates={
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
                },
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.commit()

    def create_environments(self):
        # Stateless
        self._db.add(
            PublicationEnvironmentTable(
                UUID=uuid.UUID("90000002-0000-0000-0000-000000000001"),
                Title="Stateless",
                Description="",
                Province_ID="pv28",
                Authority_ID="00000001002306608000",
                Submitter_ID="00000001002306608000",
                Governing_Body_Type="provinciale_staten",
                Frbr_Country="nl",
                Frbr_Language="nld",
                Is_Active=True,
                Has_State=False,
                Can_Validate=True,
                Can_Publicate=False,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        # Pre-Prod
        self._db.add(
            PublicationEnvironmentTable(
                UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
                Title="Pre-Prod",
                Description="",
                Province_ID="pv28",
                Authority_ID="00000001002306608000",
                Submitter_ID="00000001002306608000",
                Governing_Body_Type="provinciale_staten",
                Frbr_Country="nl",
                Frbr_Language="nld",
                Is_Active=True,
                Has_State=True,
                Can_Validate=True,
                Can_Publicate=True,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )
        self._db.add(
            PublicationEnvironmentStateTable(
                UUID=uuid.UUID("90000003-0000-0000-0000-000000000001"),
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
                Adjust_On_UUID=None,
                Change_Set={},
                State={},
                Is_Activated=True,
                Activated_Datetime=self._timepoint,
                Created_Date=self._timepoint,
                Created_By_UUID=self._user,
            )
        )

        # Prod
        self._db.add(
            PublicationEnvironmentTable(
                UUID=uuid.UUID("90000002-0000-0000-0000-000000000003"),
                Title="Prod",
                Description="",
                Province_ID="pv28",
                Authority_ID="00000001002306608000",
                Submitter_ID="00000001002306608000",
                Governing_Body_Type="provinciale_staten",
                Frbr_Country="nl",
                Frbr_Language="nld",
                Is_Active=True,
                Has_State=True,
                Can_Validate=True,
                Can_Publicate=True,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )
        self._db.add(
            PublicationEnvironmentStateTable(
                UUID=uuid.UUID("90000003-0000-0000-0000-000000000002"),
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000003"),
                Adjust_On_UUID=None,
                Change_Set={},
                State={},
                Is_Activated=True,
                Activated_Datetime=self._timepoint,
                Created_Date=self._timepoint,
                Created_By_UUID=self._user,
            )
        )

        self._db.commit()

    def create_area_of_jurisdictions(self):
        self._db.add(
            PublicationAreaOfJurisdictionTable(
                UUID=uuid.UUID("90000004-0000-0000-0000-000000000001"),
                Administrative_Borders_ID="002000000000000000009928",
                Administrative_Borders_Domain="NL.BI.BestuurlijkGebied",
                Administrative_Borders_Date=datetime.strptime("2023-09-29", "%Y-%m-%d").date(),
                Created_Date=self._timepoint,
                Created_By_UUID=self._user,
            )
        )

        self._db.commit()

    def create_publication(self):
        self._db.add(
            PublicationTable(
                UUID=uuid.UUID("90000005-0000-0000-0000-000000000001"),
                Module_ID=1,
                Document_Type=DocumentType.VISION.value,
                Template_UUID=uuid.UUID("90000001-0000-0000-0000-000000000001"),
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.commit()

    def create_publication_version(self):
        self._db.add(
            PublicationVersionTable(
                UUID=uuid.UUID("90000006-0000-0000-0000-000000000001"),
                Publication_UUID=uuid.UUID("90000005-0000-0000-0000-000000000001"),
                Module_Status_ID=2,
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000001"),
                Procedure_Type=ProcedureType.FINAL.value,
                Bill_Metadata=(
                    BillMetadata(
                        OfficialTitle="Test: Omgevingsvisie van Zuid-Holland",
                        Subjects=[
                            Onderwerp.ruimtelijke_ordening.name,
                        ],
                        Jurisdictions=[
                            Rechtsgebied.omgevingsrecht.name,
                        ],
                    )
                ).dict(),
                Bill_Compact=BillCompact(
                    Preamble="<Al>Vaststellingsbesluit Omgevingsvisie Provincie Zuid-Holland.</Al>",
                    Closing="<Al>Om de Omgevingsvisie Provincie Zuid-Holland beschikbaar te maken in het Digitale Stelsel van de Omgevingswet is het noodzakelijk dat de reeds vastgestelde Omgevingsvisie Zuid-Holland opnieuw wordt gepubliceerd en bekend gemaakt.</Al>",
                    Signed="<Al>Gedupeerde Staten</Al>",
                    AmendmentArticle='De Omgevingsvisie wordt vastgesteld zoals gegeven in <IntRef ref="cmp_A">Bijlage A</IntRef> van dit Besluit.',
                    TimeArticle="<Al>Deze Omgevingsvisie treedt in werking op [[EFFECTIVE_DATE]].</Al>",
                ).dict(),
                Procedural=Procedural(
                    SignedDate=self._timepoint.strftime("%Y-%m-%d"),
                    Procedural_Announcement_Date=self._timepoint.strftime("%Y-%m-%d"),
                ).dict(),
                Act_Metadata=ActMetadata(
                    OfficialTitle="Test: Omgevingsvisie van Zuid-Holland",
                    QuoteTitle="Test: Omgevingsvisie van Zuid-Holland",
                    Subjects=[
                        Onderwerp.ruimtelijke_ordening.name,
                    ],
                    Jurisdictions=[
                        Rechtsgebied.omgevingsrecht.name,
                    ],
                ).dict(),
                Effective_Date=self._timepoint + timedelta(days=7),
                Announcement_Date=self._timepoint + timedelta(days=7),
                Locked=False,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.commit()
