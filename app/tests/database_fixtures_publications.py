import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.extensions.areas.db.tables import AreasTable  # # noqa
from app.extensions.publications.enums import DocumentType, ProcedureType, PublicationVersionStatus
from app.extensions.publications.models import (
    ActMetadata,
    Article,
    BillCompact,
    BillMetadata,
    Procedural,
)
from app.extensions.publications.services.state.state import InitialState
from app.extensions.publications.tables.tables import (
    PublicationActTable,
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
        self.create_acts()
        self.create_publication()
        self.create_publication_version_visies()
        self.create_publication_version_maatregelen()

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
<div data-hint-element="divisietekst"><object code="visie_algemeen-1" /></div>

<div data-hint-wid-code="omgevingsvisie-custom-ambities-wrapper">
    <h1>Ambities van Zuid-Holland</h1>
    {%- for a in ambitie | sort(attribute='Title') %}
        <div data-hint-element="divisietekst"><object code="{{ a.Code }}" template="ambitie" /></div>
    {%- endfor %}
</div>

<div data-hint-wid-code="omgevingsvisie-custom-beleidsdoelen-and-beleidskeuzes-wrapper">
    <h1>Beleidsdoelen en beleidskeuzes</h1>

    {%- for d in beleidsdoel | sort(attribute='Title') %}
        {% set filtered_results = beleidskeuze | selectattr('Hierarchy_Code', 'equalto', d.Code) | list %}
        {% if filtered_results %}

            <div data-hint-wid-code="omgevingsvisie-custom-beleidsdoel-{{ d.Code }}-wrapper">
                <h1>Beleidsdoel {{ d.Title }} met beleidskeuzes</h1>
                <div data-hint-element="divisietekst"><object code="{{ d.Code }}" template="beleidsdoel" /></div>
                <div data-hint-wid-code="omgevingsvisie-custom-beleidskeuze-{{ d.Code }}-wrapper">
                    <h1>Beleidskeuzes van {{ d.Title }}</h1>
                    {%- for k in filtered_results | sort(attribute='Title') %}
                    <div data-hint-element="divisietekst"><object code="{{ k.Code }}" template="beleidskeuze" /></div>
                    {%- endfor %}
                </div>
            </div>

        {% else %}
            <div data-hint-element="divisietekst"><object code="{{ d.Code }}" template="beleidsdoel" /></div>
        {% endif %}
    {%- endfor %}
</div>

<div data-hint-element="divisietekst"><object code="visie_algemeen-2" /></div>
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
    <h6>Wat gaat de provincie doen?</h6>
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
                    "document",
                ],
                Field_Map=[
                    "UUID",
                    "Object_Type",
                    "Object_ID",
                    "Code",
                    "Hierarchy_Code",
                    "Werkingsgebied_Code",
                    "Documents",
                    "File_UUID",
                    "Filename",
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
    <div data-hint-element="divisietekst"><object code="{{ d.Code }}" template="beleidsdoel" /></div>

    {% set beleidskeuzes_codes_for_beleidsdoel = beleidskeuze | selectattr('Hierarchy_Code', 'equalto', d.Code) | map(attribute='Code') | list %}
    {% set maatregelen_for_doel = maatregel | selectattr('Hierarchy_Code', 'in', beleidskeuzes_codes_for_beleidsdoel) | list %}
    {% if maatregelen_for_doel %}

        <div data-hint-wid-code="programma-custom-beleidsdoel-{{ d.Code }}-wrapper">
            <h1>Beleidsdoel {{ d.Title }} met maatregelen</h1>
            <div data-hint-element="divisietekst"><object code="{{ d.Code }}" template="beleidsdoel" /></div>
            <div data-hint-wid-code="programma-custom-maatregel-{{ d.Code }}-wrapper">
                <h1>Maatregelen van {{ d.Title }}</h1>
                {%- for m in maatregelen_for_doel | sort(attribute='Title') %}
                <div data-hint-element="divisietekst"><object code="{{ m.Code }}" template="maatregel" /></div>
                {%- endfor %}
            </div>
        </div>

    {% else %}
        <div data-hint-element="divisietekst"><object code="{{ d.Code }}" template="beleidsdoel" /></div>
    {% endif %}
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
    <h6>Wat gaat de provincie doen?</h6>
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

{% if documents | length > 0 %}
    <h6>Documenten</h6>
    <ul data-hint-wid-code="programma-custom-maatregel-{{ o.Code }}-documenten">
        {%- for d in documents | sort(attribute='Title') %}
        <li><p><a href="#" data-hint-wid-code="document-{{ o.Code }}-{{ d.Code }}-ref" data-hint-type="document" data-hint-document-uuid="{{ d.UUID }}">{{ d.Title }}</a></p></li>
        {%- endfor %}
    </ul>
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
        env_stateless = PublicationEnvironmentTable(
            UUID=uuid.UUID("90000002-0000-0000-0000-000000000001"),
            Code="STATELESS",
            Title="Stateless",
            Description="",
            Province_ID="pv28",
            Authority_ID="00000000000000000000",
            Submitter_ID="00000000000000000000",
            Governing_Body_Type="provinciale_staten",
            Frbr_Country="nl",
            Frbr_Language="nld",
            Is_Active=True,
            Has_State=False,
            Can_Validate=True,
            Can_Publicate=False,
            Is_Locked=False,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user,
            Modified_By_UUID=self._user,
        )
        self._db.add(env_stateless)
        self._db.flush()

        # Pre-Prod
        env_preprod = PublicationEnvironmentTable(
            UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
            Code="PRE",
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
            Is_Locked=False,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user,
            Modified_By_UUID=self._user,
        )
        self._db.add(env_preprod)
        self._db.flush()

        state_preprod = PublicationEnvironmentStateTable(
            UUID=uuid.UUID("90000003-0000-0000-0000-000000000001"),
            Environment_UUID=env_preprod.UUID,
            Adjust_On_UUID=None,
            State=(InitialState().state_dict()),
            Is_Activated=True,
            Activated_Datetime=self._timepoint,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user,
        )
        self._db.add(state_preprod)
        self._db.flush()
        env_preprod.Active_State_UUID = state_preprod.UUID
        self._db.add(env_preprod)

        # Prod
        env_prod = PublicationEnvironmentTable(
            UUID=uuid.UUID("90000002-0000-0000-0000-000000000003"),
            Code="PROD",
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
            Is_Locked=False,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user,
            Modified_By_UUID=self._user,
        )
        self._db.add(env_prod)
        self._db.flush()

        state_prod = PublicationEnvironmentStateTable(
            UUID=uuid.UUID("90000003-0000-0000-0000-000000000002"),
            Environment_UUID=env_prod.UUID,
            Adjust_On_UUID=None,
            State=(InitialState().state_dict()),
            Is_Activated=True,
            Activated_Datetime=self._timepoint,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user,
        )
        self._db.add(state_prod)
        self._db.flush()
        env_prod.Active_State_UUID = state_prod.UUID
        self._db.add(env_prod)

        self._db.commit()

    def create_area_of_jurisdictions(self):
        self._db.add(
            PublicationAreaOfJurisdictionTable(
                UUID=uuid.UUID("90000004-0000-0000-0000-000000000001"),
                Title="Provincie Zuid-Hollan",
                Administrative_Borders_ID="PV28",
                Administrative_Borders_Domain="NL.BI.BestuurlijkGebied",
                Administrative_Borders_Date=datetime.strptime("2023-09-29", "%Y-%m-%d").date(),
                Created_Date=self._timepoint - timedelta(days=30),
                Created_By_UUID=self._user,
            )
        )

        self._db.commit()

    def create_acts(self):
        self._db.add(
            PublicationActTable(
                ID=1,
                UUID=uuid.UUID("90000007-0000-0000-0000-000000000001"),
                Title="Omgevingsvisie 1 voor Stateless",
                Is_Active=True,
                Document_Type=DocumentType.VISION.value,
                Procedure_Type=ProcedureType.FINAL.value,
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000001"),
                Metadata=ActMetadata(
                    Official_Title="Inhouse: Omgevingsvisie van Zuid-Holland",
                    Quote_Title="Inhouse: Omgevingsvisie van Zuid-Holland",
                    Subjects=[
                        Onderwerp.ruimtelijke_ordening.name,
                    ],
                    Jurisdictions=[
                        Rechtsgebied.omgevingsrecht.name,
                    ],
                ).dict(),
                Metadata_Is_Locked=False,
                Work_Province_ID="pv28",
                Work_Country="nl",
                Work_Date="2024",
                Work_Other="omgevingsvisie-1",
                Withdrawal_Purpose_UUID=None,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.add(
            PublicationActTable(
                ID=2,
                UUID=uuid.UUID("90000007-0000-0000-0000-000000000002"),
                Title="Omgevingsvisie 1 voor Pre-Prod",
                Is_Active=True,
                Document_Type=DocumentType.VISION.value,
                Procedure_Type=ProcedureType.FINAL.value,
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
                Metadata=ActMetadata(
                    Official_Title="Omgevingsvisie van Zuid-Holland",
                    Quote_Title="Omgevingsvisie van Zuid-Holland",
                    Subjects=[
                        Onderwerp.ruimtelijke_ordening.name,
                    ],
                    Jurisdictions=[
                        Rechtsgebied.omgevingsrecht.name,
                    ],
                ).dict(),
                Metadata_Is_Locked=False,
                Work_Province_ID="pv28",
                Work_Country="nl",
                Work_Date="2024",
                Work_Other="omgevingsvisie-1",
                Withdrawal_Purpose_UUID=None,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.add(
            PublicationActTable(
                ID=3,
                UUID=uuid.UUID("90000007-0000-0000-0000-000000000003"),
                Title="Ontwerp Omgevingsvisie 1 voor Pre-Prod",
                Is_Active=True,
                Document_Type=DocumentType.VISION.value,
                Procedure_Type=ProcedureType.DRAFT.value,
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
                Metadata=ActMetadata(
                    Official_Title="Ontwerp omgevingsvisie van Zuid-Holland",
                    Quote_Title="Ontwerp omgevingsvisie van Zuid-Holland",
                    Subjects=[
                        Onderwerp.ruimtelijke_ordening.name,
                    ],
                    Jurisdictions=[
                        Rechtsgebied.omgevingsrecht.name,
                    ],
                ).dict(),
                Metadata_Is_Locked=False,
                Work_Province_ID="pv28",
                Work_Country="nl",
                Work_Date="2024",
                Work_Other="ontwerp-omgevingsvisie-1",
                Withdrawal_Purpose_UUID=None,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.add(
            PublicationActTable(
                ID=4,
                UUID=uuid.UUID("90000007-0000-0000-0000-000000000004"),
                Title="Programma 1 voor Pre-Prod",
                Is_Active=True,
                Document_Type=DocumentType.PROGRAM.value,
                Procedure_Type=ProcedureType.FINAL.value,
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
                Metadata=ActMetadata(
                    Official_Title="Programma van Zuid-Holland",
                    Quote_Title="Programma van Zuid-Holland",
                    Subjects=[
                        Onderwerp.ruimtelijke_ordening.name,
                    ],
                    Jurisdictions=[
                        Rechtsgebied.omgevingsrecht.name,
                    ],
                ).dict(),
                Metadata_Is_Locked=False,
                Work_Province_ID="pv28",
                Work_Country="nl",
                Work_Date="2024",
                Work_Other="programma-1",
                Withdrawal_Purpose_UUID=None,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.commit()

    def create_publication(self):
        self._db.add(
            PublicationTable(
                UUID=uuid.UUID("90000005-0000-0000-0000-000000000001"),
                Module_ID=1,
                Title="Stateless Omgevingsvisie Module 1",
                Document_Type=DocumentType.VISION.value,
                Procedure_Type=ProcedureType.FINAL.value,
                Template_UUID=uuid.UUID("90000001-0000-0000-0000-000000000001"),
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000001"),
                Act_UUID=uuid.UUID("90000007-0000-0000-0000-000000000001"),
                Is_Locked=False,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )
        self._db.add(
            PublicationTable(
                UUID=uuid.UUID("90000005-0000-0000-0000-000000000002"),
                Module_ID=1,
                Title="Pre-Prod Omgevingsvisie Module 1",
                Document_Type=DocumentType.VISION.value,
                Procedure_Type=ProcedureType.FINAL.value,
                Template_UUID=uuid.UUID("90000001-0000-0000-0000-000000000001"),
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
                Act_UUID=uuid.UUID("90000007-0000-0000-0000-000000000002"),
                Is_Locked=False,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )
        self._db.add(
            PublicationTable(
                UUID=uuid.UUID("90000005-0000-0000-0000-000000000003"),
                Module_ID=1,
                Title="Pre-Prod Ontwerp Omgevingsvisie Module 1",
                Document_Type=DocumentType.VISION.value,
                Procedure_Type=ProcedureType.DRAFT.value,
                Template_UUID=uuid.UUID("90000001-0000-0000-0000-000000000001"),
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
                Act_UUID=uuid.UUID("90000007-0000-0000-0000-000000000003"),
                Is_Locked=False,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )
        self._db.add(
            PublicationTable(
                UUID=uuid.UUID("90000005-0000-0000-0000-000000000004"),
                Module_ID=1,
                Title="Pre-Prod Programma Module 1",
                Document_Type=DocumentType.VISION.value,
                Procedure_Type=ProcedureType.FINAL.value,
                Template_UUID=uuid.UUID("90000001-0000-0000-0000-000000000002"),
                Environment_UUID=uuid.UUID("90000002-0000-0000-0000-000000000002"),
                Act_UUID=uuid.UUID("90000007-0000-0000-0000-000000000004"),
                Is_Locked=False,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.commit()

    def create_publication_version_visies(self):
        self._db.add(
            PublicationVersionTable(
                UUID=uuid.UUID("90000006-0000-0000-0000-000000000001"),
                Publication_UUID=uuid.UUID("90000005-0000-0000-0000-000000000001"),
                Module_Status_ID=2,
                Bill_Metadata=(
                    BillMetadata(
                        Official_Title="Omgevingsvisie van Zuid-Holland",
                        Quote_Title="Omgevingsvisie van Zuid-Holland",
                        Subjects=[
                            Onderwerp.ruimtelijke_ordening.name,
                        ],
                        Jurisdictions=[
                            Rechtsgebied.omgevingsrecht.name,
                        ],
                    )
                ).dict(),
                Bill_Compact=BillCompact(
                    Preamble="<p>Vaststellingsbesluit Omgevingsvisie Provincie Zuid-Holland.</p>",
                    Closing="<p>Aldus vastgesteld in de vergadering van [[SIGNED_DATE]].</p>",
                    Signed="<p>Gedeputeerde Staten</p>",
                    Amendment_Article='De Omgevingsvisie wordt vastgesteld zoals gegeven in <IntRef ref="cmp_A">Bijlage A</IntRef> van dit Besluit.',
                    Time_Article="<Al>Deze Omgevingsvisie treedt in werking op [[EFFECTIVE_DATE]].</Al>",
                    Custom_Articles=[
                        Article(
                            Number="III",
                            Content="<p>Hierbij nog meer tekst</p>",
                        ),
                    ],
                ).dict(),
                Procedural=Procedural(
                    Signed_Date=self._timepoint.strftime("%Y-%m-%d"),
                    Procedural_Announcement_Date=self._timepoint.strftime("%Y-%m-%d"),
                ).dict(),
                Effective_Date=self._timepoint + timedelta(days=7),
                Announcement_Date=self._timepoint + timedelta(days=7),
                Is_Locked=False,
                Status=PublicationVersionStatus.NOT_APPLICABLE,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.add(
            PublicationVersionTable(
                UUID=uuid.UUID("90000006-0000-0000-0000-000000000002"),
                Publication_UUID=uuid.UUID("90000005-0000-0000-0000-000000000002"),
                Module_Status_ID=2,
                Bill_Metadata=(
                    BillMetadata(
                        Official_Title="Omgevingsvisie van Zuid-Holland",
                        Quote_Title="Omgevingsvisie van Zuid-Holland",
                        Subjects=[
                            Onderwerp.ruimtelijke_ordening.name,
                        ],
                        Jurisdictions=[
                            Rechtsgebied.omgevingsrecht.name,
                        ],
                    )
                ).dict(),
                Bill_Compact=BillCompact(
                    Preamble="<p>Vaststellingsbesluit Omgevingsvisie Provincie Zuid-Holland.</p>",
                    Closing="<p>Aldus vastgesteld in de vergadering van [[SIGNED_DATE]].</p>",
                    Signed="<p>Gedeputeerde Staten</p>",
                    Amendment_Article='De Omgevingsvisie wordt vastgesteld zoals gegeven in <IntRef ref="cmp_A">Bijlage A</IntRef> van dit Besluit.',
                    Time_Article="<Al>Deze Omgevingsvisie treedt in werking op [[EFFECTIVE_DATE]].</Al>",
                    Custom_Articles=[
                        Article(
                            Number="III",
                            Content="<p>Hierbij nog meer tekst</p>",
                        ),
                    ],
                ).dict(),
                Procedural=Procedural(
                    Signed_Date=self._timepoint.strftime("%Y-%m-%d"),
                    Procedural_Announcement_Date=self._timepoint.strftime("%Y-%m-%d"),
                ).dict(),
                Effective_Date=self._timepoint + timedelta(days=3),
                Announcement_Date=self._timepoint + timedelta(days=3),
                Is_Locked=False,
                Status=PublicationVersionStatus.ACTIVE,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.add(
            PublicationVersionTable(
                UUID=uuid.UUID("90000006-0000-0000-0000-000000000003"),
                Publication_UUID=uuid.UUID("90000005-0000-0000-0000-000000000002"),
                Module_Status_ID=3,
                Bill_Metadata=(
                    BillMetadata(
                        Official_Title="Omgevingsvisie van Zuid-Holland",
                        Quote_Title="Omgevingsvisie van Zuid-Holland",
                        Subjects=[
                            Onderwerp.ruimtelijke_ordening.name,
                        ],
                        Jurisdictions=[
                            Rechtsgebied.omgevingsrecht.name,
                        ],
                    )
                ).dict(),
                Bill_Compact=BillCompact(
                    Preamble="<p>Vaststellingsbesluit Omgevingsvisie Provincie Zuid-Holland.</p>",
                    Closing="<p>Aldus vastgesteld in de vergadering van [[SIGNED_DATE]].</p>",
                    Signed="<p>Gedeputeerde Staten</p>",
                    Amendment_Article='De Omgevingsvisie wordt vastgesteld zoals gegeven in <IntRef ref="cmp_A">Bijlage A</IntRef> van dit Besluit.',
                    Time_Article="<Al>Deze Omgevingsvisie treedt in werking op [[EFFECTIVE_DATE]].</Al>",
                    Custom_Articles=[
                        Article(
                            Number="III",
                            Content="<p>Hierbij nog meer tekst</p>",
                        ),
                    ],
                ).dict(),
                Procedural=Procedural(
                    Signed_Date=self._timepoint.strftime("%Y-%m-%d"),
                    Procedural_Announcement_Date=self._timepoint.strftime("%Y-%m-%d"),
                ).dict(),
                Effective_Date=self._timepoint + timedelta(days=7),
                Announcement_Date=self._timepoint + timedelta(days=7),
                Is_Locked=False,
                Status=PublicationVersionStatus.ACTIVE,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.add(
            PublicationVersionTable(
                UUID=uuid.UUID("90000006-0000-0000-0000-000000000004"),
                Publication_UUID=uuid.UUID("90000005-0000-0000-0000-000000000003"),
                Module_Status_ID=3,
                Bill_Metadata=(
                    BillMetadata(
                        Official_Title="Ontwerp Omgevingsvisie van Zuid-Holland",
                        Quote_Title="Ontwerp Omgevingsvisie van Zuid-Holland",
                        Subjects=[
                            Onderwerp.ruimtelijke_ordening.name,
                        ],
                        Jurisdictions=[
                            Rechtsgebied.omgevingsrecht.name,
                        ],
                    )
                ).dict(),
                Bill_Compact=BillCompact(
                    Preamble="<p>Ontwerp Omgevingsvisie Provincie Zuid-Holland.</p>",
                    Closing="<p>Aldus vastgesteld in de vergadering van [[SIGNED_DATE]].</p>",
                    Signed="<p>Gedeputeerde Staten</p>",
                    Amendment_Article='Het ontwerp van de Omgevingsvisie wordt vastgesteld zoals gegeven in <IntRef ref="cmp_A">Bijlage A</IntRef> van dit Besluit.',
                    Custom_Articles=[
                        Article(
                            Number="III",
                            Content="<p>Hierbij nog meer tekst</p>",
                        ),
                    ],
                ).dict(),
                Procedural=Procedural(
                    Signed_Date=self._timepoint.strftime("%Y-%m-%d"),
                    Procedural_Announcement_Date=self._timepoint.strftime("%Y-%m-%d"),
                ).dict(),
                Announcement_Date=self._timepoint + timedelta(days=7),
                Is_Locked=False,
                Status=PublicationVersionStatus.ACTIVE,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )

        self._db.commit()

    def create_publication_version_maatregelen(self):
        self._db.add(
            PublicationVersionTable(
                UUID=uuid.UUID("90000006-0000-0000-0000-000000000005"),
                Publication_UUID=uuid.UUID("90000005-0000-0000-0000-000000000004"),
                Module_Status_ID=3,
                Bill_Metadata=(
                    BillMetadata(
                        Official_Title="Programma van Zuid-Holland",
                        Quote_Title="Programma van Zuid-Holland",
                        Subjects=[
                            Onderwerp.ruimtelijke_ordening.name,
                        ],
                        Jurisdictions=[
                            Rechtsgebied.omgevingsrecht.name,
                        ],
                    )
                ).dict(),
                Bill_Compact=BillCompact(
                    Preamble="<p>Vaststellingsbesluit Programma Provincie Zuid-Holland.</p>",
                    Closing="<p>Aldus vastgesteld in de vergadering van [[SIGNED_DATE]].</p>",
                    Signed="<p>Gedeputeerde Staten</p>",
                    Amendment_Article='Het Programma wordt vastgesteld zoals gegeven in <IntRef ref="cmp_A">Bijlage A</IntRef> van dit Besluit.',
                    Time_Article="<Al>Dit Programma treedt in werking op [[EFFECTIVE_DATE]].</Al>",
                    Custom_Articles=[
                        Article(
                            Number="III",
                            Content="<p>Hierbij nog meer tekst</p>",
                        ),
                    ],
                ).dict(),
                Procedural=Procedural(
                    Signed_Date=self._timepoint.strftime("%Y-%m-%d"),
                    Procedural_Announcement_Date=self._timepoint.strftime("%Y-%m-%d"),
                ).dict(),
                Effective_Date=self._timepoint + timedelta(days=7),
                Announcement_Date=self._timepoint + timedelta(days=7),
                Is_Locked=False,
                Status=PublicationVersionStatus.ACTIVE,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user,
                Modified_By_UUID=self._user,
            )
        )
        self._db.commit()
