from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, DateTime, text, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr


class CommonMixin():
    ID = Column(Integer, nullable=False)
    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Begin_Geldigheid = Column(DateTime, nullable=False)
    Eind_Geldigheid = Column(DateTime, nullable=False)
    Created_Date = Column(DateTime, nullable=False)
    Modified_Date = Column(DateTime, nullable=False)

    @declared_attr
    def Created_By(cls):
        return Column('Created_By', ForeignKey('Gebruikers.UUID'), nullable=False)

    @declared_attr
    def Modified_By(cls):
        return Column('Modified_By', ForeignKey('Gebruikers.UUID'), nullable=False)


db = SQLAlchemy()
