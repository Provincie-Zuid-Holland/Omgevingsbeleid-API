from curses.ascii import NUL
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import over
from sqlalchemy.orm import Session, Query, load_only, aliased
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import select, label, text
from sqlalchemy.sql.expression import func

from app.core.exceptions import DatabaseError
from app.db.base_class import Base, NULL_UUID
from app.db.session import SessionLocal

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        self.db = SessionLocal()

    def get(self, uuid: str) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.UUID == uuid).first()

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.ID == id).first()

    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        try:
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            raise DatabaseError()

    def update(
        self, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        try:
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except:
            raise DatabaseError()

    def remove(self, *, id: int) -> ModelType:
        obj = self.db.query(self.model).get(id)
        try:
            self.db.delete(obj)
            self.db.commit()
            return obj
        except:
            raise DatabaseError()

    #
    # Valid 'views'
    #
    
    def latest(self, all: bool = False) -> List[ModelType]:
        partition = func.row_number().over(partition_by="ID", order_by="Modified_Date")
        row_number = label("RowNumber", partition)

        sub_query = self.db.query(self.model, row_number).subquery()
        model_alias = aliased(self.model, sub_query)

        query = (
            self.db.query(model_alias)
            .filter(sub_query.c.RowNumber == 1)
            .filter(model_alias.UUID != NULL_UUID)
        )

        if not all:
            query = query.filter(model_alias.Eind_Geldigheid > datetime.utcnow())

        # TODO filter and limit with _build_default_query
        return query.all()

    def valid(self) -> List[ModelType]:
        partition = func.row_number().over(partition_by="ID", order_by="Modified_Date")
        row_number = label("RowNumber", partition)

        sub_query = (
            self.db.query(self.model, row_number)
            .filter(self.model.Begin_Geldigheid <= datetime.utcnow())
            .subquery()
        )
        
        model_alias = aliased(self.model, sub_query)

        query = (
            self.db.query(model_alias)
            .filter(sub_query.c.RowNumber == 1)
            .filter(model_alias.UUID != NULL_UUID)
            .filter(model_alias.Eind_Geldigheid > datetime.utcnow())
        )

        # TODO filter and limit with _build_default_query
        return query.all()

    #
    # Common repository actions
    #

    def list(self, offset: int = 0, limit: int = 100, **criteria) -> List[ModelType]:
        query = self._build_filtered_query(**criteria)
        query.offset(offset).limit(limit)

        return query.all()

    def all(self, select: List = None, **criteria) -> List[ModelType]:
        """
        Fetch all available objects of this model matching
        the filter criteria and/or specified columns.

        **Example**

        ambitie.all([Ambitie.Titel], Created_Date=5)

        **Parameters**

        * `select`: A List of attributes to select
        * `criteria`: A Dict to filter by column : value
        """
        query = self._build_filtered_query(**criteria)

        # select specific columns
        if select:
            query = query.options(load_only(*select))

        return query.all()

    def find_one(self, **criteria) -> ModelType:
        query = self._build_filtered_query(**criteria)

        return query.one()
    
    def search(self, **criteria) -> Query:
        return self._build_filtered_query(**criteria)
    
    def _build_filtered_query(self, **criteria) -> Query:
        """
        Allows simply passing arguments as filter criteria
        for any model.
        """
        query = self._build_default_query()

        for criterion, value in criteria.items():
            column = getattr(self.model, criterion)

            if isinstance(value, list):
                query = query.filter(column.in_(value))
            else:
                query = query.filter(column == value)

        return query

    def _build_default_query(self) -> Query:
            query = self.db.query(self.model)
            
            # Apply 'valid' filter
            query = query.filter(self.model.UUID != NULL_UUID)

            # Default to order by ID
            if hasattr(self.model, 'Modified_Date'):
                query = query.order_by(self.model.Modified_Date.desc())
            else:
                query = query.order_by(self.model.ID.desc())
            
            return query


