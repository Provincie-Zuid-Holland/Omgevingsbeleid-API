from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base


class Gebruiker(Base):
    __tablename__ = "Gebruikers"

    @declared_attr
    def ID(cls):
        seq_name = "seq_{name}".format(name=cls.__name__)
        seq = Sequence(seq_name)
        return Column(Integer, seq, nullable=False, server_default=seq.next_value())

    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Gebruikersnaam = Column(Unicode(50), nullable=False)
    Wachtwoord = Column(Unicode)
    Rol = Column(Unicode(50), nullable=False)
    Email = Column(Unicode(265))
    Status = Column(Unicode(50), server_default=text("('Actief')"))

    @property
    def is_active(self):
        return self.Status == 'Actief'

    def as_identity(self):
        return {
            "UUID": self.UUID,
            "Gebruikersnaam": self.Gebruikersnaam,
            "Rol": self.Rol,
            "Email": self.Email,
            "Status": self.Status,
        }
