from typing import List, TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Unicode,
    text,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session

# from app.crud.crud_maatregel import CRUDMaatregel

from app.db.base_class import Base
from app.util.legacy_helpers import SearchFields

if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Maatregel  # noqa: F401
    from .maatregel import Maatregel  # noqa: F401


class Beleidskeuze_Maatregelen(Base):
    __tablename__ = "Beleidskeuze_Maatregelen"

    Beleidskeuze_UUID = Column(ForeignKey("Beleidskeuzes.UUID"), primary_key=True)
    Maatregel_UUID = Column(ForeignKey("Maatregelen.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidskeuze = relationship("Beleidskeuze", back_populates="Maatregelen")
    Maatregel = relationship("Maatregel", back_populates="Beleidskeuzes")


class Beleidsmodule_Maatregelen(Base):
    __tablename__ = "Beleidsmodule_Maatregelen"

    Beleidsmodule_UUID = Column(ForeignKey("Beleidsmodules.UUID"), primary_key=True)
    Maatregel_UUID = Column(ForeignKey("Maatregelen.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidsmodule = relationship("Beleidsmodule", back_populates="Maatregelen")
    Maatregel = relationship("Maatregel", back_populates="Beleidsmodules")


class Maatregel(Base):
    __tablename__ = "Maatregelen"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Maatregelen"
        seq = Sequence(seq_name)
        return Column(Integer, seq, nullable=False, server_default=seq.next_value())

    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Begin_Geldigheid = Column(DateTime, nullable=False)
    Eind_Geldigheid = Column(DateTime, nullable=False)
    Created_Date = Column(DateTime, nullable=False)
    Modified_Date = Column(DateTime, nullable=False)

    Created_By_UUID = Column(
        "Created_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )
    Modified_By_UUID = Column(
        "Modified_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )

    Titel = Column(Unicode, nullable=False)
    Omschrijving = Column(Unicode)
    Toelichting = Column(Unicode)
    Toelichting_Raw = Column(Unicode)
    Weblink = Column(Unicode)
    Gebied_UUID = Column("Gebied", ForeignKey("Werkingsgebieden.UUID"))
    Status = Column(Unicode(50))
    Gebied_Duiding = Column(Unicode)
    Tags = Column(Unicode)

    Aanpassing_Op_UUID = Column("Aanpassing_Op", ForeignKey("Maatregelen.UUID"))
    Eigenaar_1_UUID = Column("Eigenaar_1", ForeignKey("Gebruikers.UUID"))
    Eigenaar_2_UUID = Column("Eigenaar_2", ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_1_UUID = Column(
        "Portefeuillehouder_1", ForeignKey("Gebruikers.UUID")
    )
    Portefeuillehouder_2_UUID = Column(
        "Portefeuillehouder_2", ForeignKey("Gebruikers.UUID")
    )
    Opdrachtgever_UUID = Column("Opdrachtgever", ForeignKey("Gebruikers.UUID"))

    Created_By = relationship(
        "Gebruiker", primaryjoin="Maatregel.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Maatregel.Modified_By_UUID == Gebruiker.UUID"
    )

    Beleidskeuzes = relationship(
        Beleidskeuze_Maatregelen, back_populates="Maatregel", lazy="dynamic"
    )

    Beleidsmodules = relationship(
        "Beleidsmodule_Maatregelen", back_populates="Maatregel"
    )

    Aanpassing_Op = relationship(
        "Maatregel", primaryjoin="Maatregel.Aanpassing_Op_UUID == Maatregel.UUID"
    )
    Eigenaar_1 = relationship(
        "Gebruiker", primaryjoin="Maatregel.Eigenaar_1_UUID == Gebruiker.UUID"
    )
    Eigenaar_2 = relationship(
        "Gebruiker", primaryjoin="Maatregel.Eigenaar_2_UUID == Gebruiker.UUID"
    )
    Portefeuillehouder_1 = relationship(
        "Gebruiker", primaryjoin="Maatregel.Portefeuillehouder_1_UUID == Gebruiker.UUID"
    )
    Portefeuillehouder_2 = relationship(
        "Gebruiker", primaryjoin="Maatregel.Portefeuillehouder_2_UUID == Gebruiker.UUID"
    )
    Opdrachtgever = relationship(
        "Gebruiker", primaryjoin="Maatregel.Opdrachtgever_UUID == Gebruiker.UUID"
    )
    Gebied = relationship(
        "Werkingsgebied", primaryjoin="Maatregel.Gebied_UUID == Werkingsgebied.UUID"
    )
    Gebiedsprogrammas = relationship(
        "Maatregel_Gebiedsprogrammas", 
        back_populates="Maatregel"
    )

    @hybrid_property
    def All_Beleidskeuzes(self):
        return self.Beleidskeuzes.all()

    @hybrid_property
    def Valid_Beleidskeuzes(self):
        from app.crud.crud_beleidskeuze import CRUDBeleidskeuze

        valid_beleidskeuzes = CRUDBeleidskeuze.valid_view_static()
        return self.Beleidskeuzes.join(
            valid_beleidskeuzes,
            valid_beleidskeuzes.UUID == Beleidskeuze_Maatregelen.Beleidskeuze_UUID,
        ).all()

    @hybrid_property
    def Effective_Version(self):
        from app.crud.crud_maatregel import CRUDMaatregel

        valid = CRUDMaatregel.valid_view_static()
        return (
            object_session(self)
            .query(Maatregel)
            .filter(Maatregel.ID == self.ID)
            .join(valid, valid.UUID == Maatregel.UUID)
            .first()
            .UUID
        )

    # @property
    # def Effective_Version(self):
    #     query = """
    #             SELECT UUID FROM Valid_maatregelen
    #             WHERE ID = :BKID
    #             """
    #     params = {"BKID": self.ID}
    #     try:
    #         result = object_session(self).execute(query, params=params).one()
    #         return str(result.UUID)
    #     except NoResultFound:
    #         return None

    @classmethod
    def get_search_fields(cls):
        return SearchFields(title=cls.Titel, description=[cls.Toelichting])

    @classmethod
    def get_allowed_filter_keys(cls) -> List[str]:
        return [
            "ID",
            "UUID",
            "Begin_Geldigheid",
            "Eind_Geldigheid",
            "Created_Date",
            "Modified_Date",
            "Created_By_UUID",
            "Modified_By_UUID",
            "Titel",
            "Omschrijving",
            "Toelichting",
            "Toelichting_Raw",
            "Weblink",
            "Gebied_UUID",
            "Gebied_Duiding",
            "Status",
            "Tags",
            "Aanpassing_Op_UUID",
            "Eigenaar_1_UUID",
            "Eigenaar_2_UUID",
            "Portefeuillehouder_1_UUID",
            "Portefeuillehouder_2_UUID",
            "Opdrachtgever_UUID",
        ]
