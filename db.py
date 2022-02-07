from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base


class CommonMixin():
    ID = Column(Integer)
    UUID = Column(String(40), primary_key=True)
    Begin_Geldigheid = Column(DateTime)
    Eind_Geldigheid = Column(DateTime)
    Created_By = Column(String(40))
    Created_Date = Column(DateTime)
    Modified_By = Column(String(40))
    Modified_Date = Column(DateTime)


Base = declarative_base()
db = SQLAlchemy()
