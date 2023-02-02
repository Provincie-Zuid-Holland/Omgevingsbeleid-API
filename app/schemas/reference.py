from typing import Any, Optional

from pydantic.main import BaseModel
from pydantic.utils import GetterDict


# Reverse Relations


class GenericReferenceUpdate(BaseModel):
    UUID: str
    Koppeling_Omschrijving: str


class DefaultReferenceSchema(BaseModel):
    ID: int
    UUID: str
    Titel: Optional[str]

    class Config:
        orm_mode = True
        # getter_dict = <GETTER>


class RelatedValidBeleidskeuzeGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._obj.Valid_Beleidskeuze, key)


class ValidBeleidskeuzeReference(DefaultReferenceSchema):
    class Config:
        getter_dict = RelatedValidBeleidskeuzeGetter


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


class RelatedBeleidsdoelGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._obj.Beleidsdoel, key)


class BeleidsdoelReference(DefaultReferenceSchema):
    class Config:
        getter_dict = RelatedBeleidsdoelGetter


class RelatedGebiedsprogrammaGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._obj.Gebiedsprogramma, key)


class GebiedsprogrammaReference(DefaultReferenceSchema):
    class Config:
        getter_dict = RelatedGebiedsprogrammaGetter
