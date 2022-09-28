from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query
from sqlalchemy.orm import Query, Session, aliased, load_only
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import label
from sqlalchemy.sql.elements import ColumnElement, Label
from sqlalchemy.sql.expression import func

from app.crud.base import CRUDBase
from app.db.base_class import BaseTimeStamped, NULL_UUID
from app.models.beleidsrelatie import Beleidsrelatie
from app.schemas.beleidsrelatie import BeleidsrelatieCreate, BeleidsrelatieUpdate
from app.schemas.filters import FilterCombiner, Filters

class CRUDBeleidsrelatie(
    CRUDBase[Beleidsrelatie, BeleidsrelatieCreate, BeleidsrelatieUpdate]
):
    def valid(
        self,
        ID: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
        filters: Optional[Filters] = None,
    ) -> List[ModelType]:
        # List current model with valid view filters applied
        query = self._build_valid_view_filter(ID=ID, filters=filters)

        query = query.offset(offset)

        if limit != -1:
            query = query.limit(limit)

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

        return query.order_by(model_alias.ID.desc())

    def _build_valid_view_filter(
        self,
        ID: Optional[int] = None,
        filters: Optional[Filters] = None,
        as_subquery: Optional[bool] = False,
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

        if as_subquery:
            return query.subquery()

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

beleidsrelatie = CRUDBeleidsrelatie(Beleidsrelatie)
