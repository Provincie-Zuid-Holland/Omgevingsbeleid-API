import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar, Literal

from pydantic import Field

from app.core.db import Base
from app.core.tables.publications import PublicationTemplateTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationTemplateSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "modified_by_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None
    title: str
    description: str
    is_active: bool
    document_type: Literal["omgevingsvisie", "programma"] = "omgevingsvisie"

    """
    ["visie_algemeen", "ambitie", "beleidsdoel", "beleidskeuze", "gebiedengroep", "gebied", "gebiedsaanwijzing"]
    """
    object_types: list[str] = Field(default_factory=list)

    """
    <div data-hint-element="divisietekst"><object code="beleidsdoel-1" /></div>
    <div data-hint-element="divisietekst"><object code="beleidskeuze-1" /></div>
    """
    text_template: str

    """
    {
        "beleidsdoel":
            ```
            <h1>{{ o.Title }}</h1>
            <!--[OBJECT-CODE: {{ o.Code }}]-->
            {{ o.Description | default('', true)}}
            ```
        "beleidskeuze": ...
    }
    """
    object_templates: dict[str, str] = Field(default_factory=dict)

    """
    {
        "beleidsdoel": [
            "Title",
            "Description"
        ],
        "beleidskeuze": [
            "Title",
            "Description",
            "Explanation",
            "Gebiedengroep_Code"
        ]
    }
    """
    object_field_map: dict[str, str | list[str]] = Field(default_factory=dict)

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationTemplatePrefillHandler(BasePrefillHandler[PublicationTemplateSpec]):
    def fill(self, record: Record[PublicationTemplateSpec], context: PrefillContext) -> Record[PublicationTemplateSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationTemplatePersistHandler(BasePersistHandler[PublicationTemplateSpec]):
    def to_rows(self, record: Record[PublicationTemplateSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationTemplateSpec = record.spec
        return [
            PublicationTemplateTable(
                id=spec.id,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                title=spec.title,
                description=spec.description,
                is_active=spec.is_active,
                document_type=spec.document_type,
                object_types=spec.object_types,
                object_field_map=spec.object_field_map,
                text_template=spec.text_template,
                object_templates=spec.object_templates,
            )
        ]
