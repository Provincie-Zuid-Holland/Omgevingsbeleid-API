from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base


# class Base_DB_Schema(db.Model):
#     ID = Column(Integer)
#     UUID = Column(UUIDType(binary=False), primary_key=True)
#     Begin_Geldigheid = Column(DateTime)
#     Eind_Geldigheid = Column(DateTime)
#     Created_By = Column(UUIDType(binary=False))
#     Created_Date = Column(DateTime)
#     Modified_By = Column(UUIDType(binary=False))
#     Modified_Date = Column(DateTime)

# Base = declarative_base(cls=Base)


class CommonMixin():
    ID = Column(Integer)
    UUID = Column(UUIDType(binary=False), primary_key=True)
    Begin_Geldigheid = Column(DateTime)
    Eind_Geldigheid = Column(DateTime)
    Created_By = Column(UUIDType(binary=False))
    Created_Date = Column(DateTime)
    Modified_By = Column(UUIDType(binary=False))
    Modified_Date = Column(DateTime)


Base = declarative_base()
db = SQLAlchemy()
