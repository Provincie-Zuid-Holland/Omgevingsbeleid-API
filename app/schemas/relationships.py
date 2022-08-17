from typing import Any, Optional
from pydantic import BaseModel
from pydantic.utils import GetterDict

# Ambitie


class AmbitieShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str

    class Config:
        orm_mode = True


class RelatedAmbitieGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .ambitie import AmbitieInDB

        keys = AmbitieInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Ambitie, key)
        else:
            return super(RelatedAmbitieGetter, self).get(key, default)


class RelatedAmbitie(AmbitieShortInline):
    class Config:
        getter_dict = RelatedAmbitieGetter


# Beleidsdoel


class BeleidsdoelShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str

    class Config:
        orm_mode = True


class RelatedBeleidsdoelGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .beleidsdoel import BeleidsdoelInDB

        keys = BeleidsdoelInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Beleidsdoel, key)
        else:
            return super(RelatedBeleidsdoelGetter, self).get(key, default)


class RelatedBeleidsdoel(BeleidsdoelShortInline):
    class Config:
        getter_dict = RelatedBeleidsdoelGetter


# Beleidskeuze


class BeleidskeuzeShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str

    class Config:
        orm_mode = True


class RelatedBeleidskeuzeGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .beleidskeuze import BeleidskeuzeInDB

        keys = BeleidskeuzeInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Beleidskeuze, key)
        else:
            return super(RelatedBeleidskeuzeGetter, self).get(key, default)


class RelatedBeleidskeuze(BeleidskeuzeShortInline):
    class Config:
        getter_dict = RelatedBeleidskeuzeGetter


# Beleidsmodule


class BeleidsmoduleShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str
    Koppeling_Omschrijving: Optional[str]

    class Config:
        orm_mode = True


class RelatedBeleidsmoduleGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .beleidsmodule import BeleidsmoduleInDB

        keys = BeleidsmoduleInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Beleidskeuze, key)
        else:
            return super(RelatedBeleidsmoduleGetter, self).get(key, default)


class RelatedBeleidsmodule(BeleidsmoduleShortInline):
    class Config:
        getter_dict = RelatedBeleidsmoduleGetter


# Gebiedsprogramma


class GebiedsprogrammaShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str
    Koppeling_Omschrijving: Optional[str]

    class Config:
        orm_mode = True


class RelatedGebiedsprogrammaGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .gebiedsprogramma import GebiedsprogrammaInDB

        keys = GebiedsprogrammaInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Gebiedsprogramma, key)
        else:
            return super(RelatedGebiedsprogrammaGetter, self).get(key, default)


class RelatedGebiedsprogramma(GebiedsprogrammaShortInline):
    class Config:
        getter_dict = RelatedGebiedsprogrammaGetter


# Gebruiker


class GebruikerInline(BaseModel):
    Gebruikersnaam: str
    Rol: str
    Status: str
    UUID: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Maatregel


class RelatedMaatregelShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str
    Koppeling_Omschrijving: Optional[str]

    class Config:
        orm_mode = True


class RelatedMaatregelGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .maatregel import MaatregelInDB

        keys = MaatregelInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Maatregel, key)
        else:
            return super(RelatedMaatregelGetter, self).get(key, default)


class RelatedMaatregel(RelatedMaatregelShortInline):
    class Config:
        getter_dict = RelatedMaatregelGetter


# Werkingsgebieden


class WerkingsgebiedShortInline(BaseModel):
    ID: int
    UUID: str
    Werkingsgebied: str

    class Config:
        orm_mode = True
