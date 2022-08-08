from datetime import datetime
from os import wait
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from h11 import Data
from app.schemas.filters import FilterCombiner, Filters

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, Query, load_only, aliased
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import label
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.elements import ColumnElement, Label

from app.core.exceptions import DatabaseError, FilterNotAllowed
from app.db.base_class import Base, BaseTimeStamped, NULL_UUID
from app.db.session import SessionLocal

ModelType = TypeVar("ModelType", bound=BaseTimeStamped)
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
        self.db: Session = SessionLocal()

    def get(self, uuid: str) -> ModelType:
        return self.db.query(self.model).filter(self.model.UUID == uuid).one()

    def create(self, *, obj_in: CreateSchemaType, by_uuid: str) -> ModelType:
        obj_in_data = jsonable_encoder(
            obj_in,
            custom_encoder={
                datetime: lambda dt: dt,
            },
        )

        request_time = datetime.now()

        obj_in_data["Created_By_UUID"] = by_uuid
        obj_in_data["Modified_By_UUID"] = by_uuid
        obj_in_data["Created_Date"] = request_time
        obj_in_data["Modified_Date"] = request_time

        db_obj = self.model(**obj_in_data)

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
    # Valid/Latest 'views'
    #

    def latest(
        self,
        all: bool = False,
        offset: int = 0,
        limit: int = 20,
        filters: Optional[Filters] = None,
    ) -> List[ModelType]:
        # List current model with latest view filters applied
        query = self._build_latest_view_filter(all, filters)
        query = query.offset(offset).limit(limit)

        return query.all()

    def get_latest_by_id(self, id: int) -> Optional[ModelType]:
        """
        Fetch the last version of a given Lineage
        """
        results = self.latest(filters=Filters({"ID": id}))

        if len(results):
            return results[0]

        return None

    def valid(
        self,
        ID: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
        filters: Optional[Filters] = None,
    ) -> List[ModelType]:
        # List current model with valid view filters applied
        query = self._build_valid_view_filter(ID=ID, filters=filters)
        query = query.offset(offset).limit(limit)

        return query.all()

    def _build_latest_view_filter(
        self, all: bool, filters: Optional[Filters] = None
    ) -> Query:
        """
        Retrieve a model with the 'Latest' view filters applied.
        Defaults to:
        - distinct ID's by latest modified
        - no null UUID row
        - Eind_Geldigheid in the future

        **Parameters**

        * `all`: If true, omits Eind_Geldigheid check
        """

        row_number = self._add_rownumber_latest_id()
        sub_query: Query = self.db.query(self.model, row_number).subquery("inner")

        model_alias: AliasedClass = aliased(
            element=self.model, alias=sub_query, name="inner", adapt_on_names=True
        )

        query: Query = (
            self.db.query(model_alias)
            .filter(sub_query.c.RowNumber == 1)
            .filter(model_alias.UUID != NULL_UUID)
        )

        if not all:
            query = query.filter(model_alias.Eind_Geldigheid > datetime.utcnow())

        query = self._build_filtered_query(
            query=query, model=model_alias, filters=filters
        )

        # query = query.filter(model_alias.ID == 5)

        return query.order_by(model_alias.ID.desc())

    def _build_valid_view_filter(
        self, ID: Optional[int] = None, filters: Optional[Filters] = None
    ) -> Query:
        """
        Retrieve a model with the 'Valid' view filters applied.
        Defaults to:
        - distinct ID's by latest modified
        - no null UUID row
        - Eind_Geldigheid in the future
        - Begin_Geldigheid today or in the past
        """

        row_number = self._add_rownumber_latest_id()

        sub_query: Query = (
            self.db.query(self.model, row_number)
            .filter(self.model.Begin_Geldigheid <= datetime.utcnow())
            .subquery("inner")
        )

        model_alias: AliasedClass = aliased(
            element=self.model, alias=sub_query, name="inner", adapt_on_names=True
        )

        query: Query = (
            self.db.query(model_alias)
            .filter(sub_query.c.RowNumber == 1)
            .filter(model_alias.UUID != NULL_UUID)
            .filter(model_alias.Eind_Geldigheid > datetime.utcnow())
        )

        if ID is not None:
            query = query.filter(model_alias.ID == ID)

        query = self._build_filtered_query(
            query=query, model=model_alias, filters=filters
        )

        return query.order_by(model_alias.ID.desc())

    def _add_rownumber_latest_id(self) -> Label:
        """
        Builds sql expression that assigns RowNumber 1 to the latest ID
        """
        partition: ColumnElement = func.row_number().over(
            partition_by=self.model.ID, order_by=self.model.Modified_Date.desc()
        )
        return label("RowNumber", partition)

    #
    # Common repository actions
    #

    def list(
        self, offset: int = 0, limit: int = 100, filters: Optional[Filters] = None
    ) -> List[ModelType]:
        query = self._build_filtered_query(filters=filters)
        query.offset(offset).limit(limit)

        return query.all()

    def all(
        self, select: Optional[List] = None, filters: Optional[Filters] = None
    ) -> List[ModelType]:
        """
        Fetch all available objects of this model matching
        the filter criteria and/or specified columns.

        **Example**

        ambitie.all([Ambitie.Titel], ID=5)

        **Parameters**

        * `select`: A List of attributes to select
        * `criteria`: A Dict to filter by column : value
        """
        query = self._build_filtered_query(filters=filters)

        # select specific columns
        if select:
            query = query.options(load_only(*select))

        return query.all()

    def find_one(self, filters: Optional[Filters] = None) -> ModelType:
        query = self._build_filtered_query(filters=filters)

        return query.one()

    def search(self, **criteria) -> Query:
        return self._build_filtered_query(**criteria)

    def _build_filtered_query(
        self,
        query: Optional[Query] = None,
        model: Optional[Type[ModelType]] = None,
        filters: Optional[Filters] = None,
    ) -> Query:
        """
        Allows simply passing arguments as filter criteria
        for any model.
        """
        if query is None:
            query = self._build_default_query()

        if model is None:
            model = self.model

        if filters is None:
            return query

        allowed_filter_keys = model.get_allowed_filter_keys()

        for clause in filters.clauses:
            expressions = []

            for item in clause.items:
                if item.key not in allowed_filter_keys:
                    raise FilterNotAllowed(filter=item.key)

                column = getattr(model, item.key)
                expressions.append(column == item.value)

            if expressions:
                if clause.combiner == FilterCombiner.OR:
                    query = query.filter(or_(*expressions))
                else:
                    query = query.filter(and_(*expressions))

        return query

    def _build_default_query(self, query: Optional[Query] = None) -> Query:
        if query is None:
            query = self.db.query(self.model)

        # Apply 'valid' filter
        query = query.filter(self.model.UUID != NULL_UUID)

        # Default to order by ID
        if hasattr(self.model, "Modified_Date"):
            query = query.order_by(self.model.Modified_Date.desc())
        else:
            query = query.order_by(self.model.ID.desc())

        return query
