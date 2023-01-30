from typing import Any, NewType, Optional

from pydantic.main import BaseModel
from pydantic.utils import GetterDict

from app.models import (
    Ambitie,
    Belang,
    Beleidsdoel,
    Beleidsprestatie,
    Beleidsregel,
    Maatregel,
    Thema,
    Verordening,
    Werkingsgebied,
)
from app.models.beleidskeuze import Beleidskeuze
from app.models.gebiedsprogrammas import Gebiedsprogramma
from app.schemas.common import create_pydantic_model


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


# Entity getters
class AmbitieGetter(DefaultGetter):
    REF_NAME = "Ambitie"


class RelatedAmbitie(DefaultRelatedSchema):
    Object: NewType("AmbitieInline", create_pydantic_model(Ambitie))

    class Config:
        getter_dict = AmbitieGetter


class BelangGetter(DefaultGetter):
    REF_NAME = "Belang"


class RelatedBelang(DefaultRelatedSchema):
    Object: NewType("BelangInline", create_pydantic_model(Belang))

    class Config:
        getter_dict = BelangGetter


class BeleidskeuzeGetter(DefaultGetter):
    REF_NAME = "Beleidskeuze"


class RelatedBeleidskeuze(DefaultRelatedSchema):
    Object: NewType("BeleidskeuzeInline", create_pydantic_model(Beleidskeuze))
    class Config:
        getter_dict = BeleidskeuzeGetter


class BeleidsprestatieGetter(DefaultGetter):
    REF_NAME = "Beleidsprestatie"


class RelatedBeleidsprestatie(DefaultRelatedSchema):
    Object: NewType("BeleidsprestatieInline", create_pydantic_model(Beleidsprestatie))

    class Config:
        getter_dict = BeleidsprestatieGetter


class BeleidsregelGetter(DefaultGetter):
    REF_NAME = "Beleidsregel"


class RelatedBeleidsregel(DefaultRelatedSchema):
    Object: NewType("BeleidsregelInline", create_pydantic_model(Beleidsregel))

    class Config:
        getter_dict = BeleidsregelGetter


class GebiedsprogrammaGetter(DefaultGetter):
    REF_NAME = "Gebiedsprogramma"


class RelatedGebiedsprogramma(DefaultRelatedSchema):
    Object: NewType("GebiedsprogrammaInline",
                    create_pydantic_model(Gebiedsprogramma))
    class Config:
        getter_dict = GebiedsprogrammaGetter


class ThemaGetter(DefaultGetter):
    REF_NAME = "Thema"


class RelatedThema(DefaultRelatedSchema):
    Object: NewType("ThemaInline", create_pydantic_model(Thema))

    class Config:
        getter_dict = ThemaGetter


class VerordeningenGetter(DefaultGetter):
    REF_NAME = "Verordeningen"


class RelatedVerordeningen(DefaultRelatedSchema):
    Object: NewType("VerordeningInline", create_pydantic_model(Verordening))

    class Config:
        getter_dict = VerordeningenGetter


class WerkingsgebiedGetter(DefaultGetter):
    REF_NAME = "Werkingsgebied"


class RelatedWerkingsgebied(DefaultRelatedSchema):
    Object: NewType("WerkingsgebiedInline", create_pydantic_model(Werkingsgebied))

    class Config:
        getter_dict = WerkingsgebiedGetter


class BeleidsdoelGetter(DefaultGetter):
    REF_NAME = "Beleidsdoel"


class RelatedBeleidsdoel(DefaultRelatedSchema):
    Object: NewType("BeleidsdoelInline", create_pydantic_model(Beleidsdoel))

    class Config:
        getter_dict = BeleidsdoelGetter


class MaatregelGetter(DefaultGetter):
    REF_NAME = "Maatregel"


class RelatedMaatregel(DefaultRelatedSchema):
    Object: NewType("MaatregelInline", create_pydantic_model(Maatregel))

    class Config:
        getter_dict = MaatregelGetter
