from typing import Dict, List, Literal, Optional, Sequence, Union
import uuid

from pydantic import Field

from app.core.db.base import Base
from app.core.tables.publications import PublicationTemplateTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    Spec,
    Record,
    PrimaryKey,
    PersistContext,
    BasePersistHandler,
)

from datetime import datetime
from typing import ClassVar, Set


from tests.fixtures.internal.types import (
    Link,
)


class PublicationTemplateSpec(Spec):
    __link_fields__: ClassVar[Set[str]] = {
        "Created_By_UUID",
        "Modified_By_UUID",
    }

    UUID: Optional[uuid.UUID] = None
    Title: str
    Description: str
    Is_Active: bool = True

    Document_Type: Union[Literal["omgevingsvisie"], Literal["programma"]] = "omgevingsvisie"

    """
    ["visie_algemeen", "ambitie", "beleidsdoel", "beleidskeuze", "gebiedengroep", "gebied", "gebiedsaanwijzing"]
    """
    Object_Types: List[str] = Field(default_factory=list)

    """
    <div data-hint-element="divisietekst"><object code="beleidsdoel-1" /></div>
    <div data-hint-element="divisietekst"><object code="beleidskeuze-1" /></div>
    """
    Text_Template: str

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
    Object_Templates: Dict[str, str] = Field(default_factory=dict)

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
    Object_Field_Map: Dict[str, List[str]] = Field(default_factory=dict)

    Created_Date: Optional[datetime] = None
    Created_By_UUID: Optional[Link] = None
    Modified_Date: Optional[datetime] = None
    Modified_By_UUID: Optional[Link] = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID


class PublicationTemplatePrefillHandler(BasePrefillHandler[PublicationTemplateSpec]):
    def fill(self, record: Record[PublicationTemplateSpec], context: PrefillContext) -> Record[PublicationTemplateSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid4()

        return record


class PublicationTemplatePersistHandler(BasePersistHandler[PublicationTemplateSpec]):
    def to_rows(self, record: Record[PublicationTemplateSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationTemplateSpec = record.spec
        return [
            PublicationTemplateTable(
                UUID=spec.UUID,
                Title=spec.Title,
                Description=spec.Description,
                Is_Active=spec.Is_Active,
                Document_Type=spec.Document_Type,
                Object_Types=spec.Object_Types,
                Text_Template=spec.Text_Template,
                Object_Templates=spec.Object_Templates,
                Object_Field_Map=spec.Object_Field_Map,
                Created_Date=spec.Created_Date,
                Created_By_UUID=spec.Created_By_UUID,
                Modified_Date=spec.Modified_Date,
                Modified_By_UUID=spec.Modified_By_UUID,
            )
        ]
