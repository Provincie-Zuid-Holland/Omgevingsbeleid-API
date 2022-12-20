from datetime import datetime
from typing import Any, Optional

from pydantic.main import BaseModel
from pydantic.utils import GetterDict

# Relations
class GenericReferenceUpdate(BaseModel):
    UUID: str
    Koppeling_Omschrijving: str


# Inline
class BeleidskeuzeShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str

    class Config:
        orm_mode = True


class GebruikerInline(BaseModel):
    Gebruikersnaam: str
    Rol: str
    Status: str
    UUID: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Default getter schemas used for many<->many relations having additional fields
# By overwriting pydantics GetterDict we ensure the joined object in the
# associasion table can be returned using standard schemas.
#
# Inherit from or overwrite RelatedSchema to change per case if needed.
# REF_NAME is the ORM attribute name of the joined object in associason.
#
# Fields from both the assoc and joinec object can be added to the RelatedSchema
# to be serialized.
#

# Generic
class DefaultGetter(GetterDict):
    REF_NAME: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:
        if (key == "Object") and (self.REF_NAME is not None):
            return getattr(self._obj, self.REF_NAME).__dict__
        else:
            return getattr(self._obj, key, default)


class DefaultRelatedSchema(BaseModel):
    Koppeling_Omschrijving: Optional[str]
    Object: Optional[Any]

    class Config:
        orm_mode = True
        getter_dict = DefaultGetter


#
# Entity getters
class AmbitieGetter(DefaultGetter):
    REF_NAME = "Ambitie"


class RelatedAmbitie(DefaultRelatedSchema):
    class Config:
        getter_dict = AmbitieGetter


class BelangGetter(DefaultGetter):
    REF_NAME = "Belang"


class RelatedBelang(DefaultRelatedSchema):
    class Config:
        getter_dict = BelangGetter


class BeleidskeuzeGetter(DefaultGetter):
    REF_NAME = "Beleidskeuze"


class RelatedBeleidskeuze(DefaultRelatedSchema):
    class Config:
        getter_dict = BeleidskeuzeGetter


class BeleidsprestatieGetter(DefaultGetter):
    REF_NAME = "Beleidsprestatie"


class RelatedBeleidsprestatie(DefaultRelatedSchema):
    class Config:
        getter_dict = BeleidsprestatieGetter


class BeleidsregelGetter(DefaultGetter):
    REF_NAME = "Beleidsregel"


class RelatedBeleidsregel(DefaultRelatedSchema):
    class Config:
        getter_dict = BeleidsregelGetter


class ThemaGetter(DefaultGetter):
    REF_NAME = "Thema"


class RelatedThema(DefaultRelatedSchema):
    class Config:
        getter_dict = ThemaGetter


class VerordeningenGetter(DefaultGetter):
    REF_NAME = "Verordeningen"


class RelatedVerordeningen(DefaultRelatedSchema):
    class Config:
        getter_dict = VerordeningenGetter


class WerkingsgebiedGetter(DefaultGetter):
    REF_NAME = "Werkingsgebied"


class RelatedWerkingsgebied(DefaultRelatedSchema):
    class Config:
        getter_dict = WerkingsgebiedGetter


class BeleidsdoelGetter(DefaultGetter):
    REF_NAME = "Beleidsdoel"


class RelatedBeleidsdoel(DefaultRelatedSchema):
    class Config:
        getter_dict = BeleidsdoelGetter


class MaatregelGetter(DefaultGetter):
    REF_NAME = "Maatregel"


class RelatedMaatregel(DefaultRelatedSchema):
    class Config:
        getter_dict = MaatregelGetter


# Other Refs
class DefaultReferenceSchema(BaseModel):
    ID: int
    UUID: str
    Titel: Optional[str]

    class Config:
        orm_mode = True
        # getter_dict = <GETTER>


class RelatedBeleidskeuzeGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._obj.Beleidskeuze, key)


class BeleidskeuzeReference(DefaultReferenceSchema):
    class Config:
        getter_dict = RelatedBeleidskeuzeGetter


class RelatedBeleidsmoduleGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._obj.Beleidsmodule, key)


class BeleidsmoduleReference(DefaultReferenceSchema):
    class Config:
        getter_dict = RelatedBeleidsmoduleGetter


# Other shared schemas


class LatestVersionInline(BaseModel):
    """
    Schema listing inline version of entity showing the latest
    version available.

    Used in /edits for Beleidskeuzes & Maatregelen
    """

    ID: int
    UUID: str

    Modified_Date: datetime
    Status: str
    Titel: str

    Effective_Version: Optional[str]
    Type: str

    class Config:
        orm_mode = True
