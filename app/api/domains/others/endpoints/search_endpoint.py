from datetime import datetime, timezone
from typing import Annotated, Generic, List, Optional, Dict, Self, Set

from bs4 import BeautifulSoup
from dependency_injector.wiring import Provide
from fastapi import Body, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import Select, asc, desc, func, literal, or_, select, union_all
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.modules.services.module_objects_to_models_parser import ModuleObjectsToModelsParser
from app.api.domains.others.types import TModel
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import (
    PagedResponse,
    PaginatedQueryResult,
    SimplePagination,
    query_paginated_no_scalars,
)
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from app.core.tables.objects import ObjectsTable


class SearchEndpointContext(BaseEndpointContext):
    model_map: Dict[str, str]
    allowed_object_types: Set[str]
    search_columns: Set[str]
    used_columns: Set[str]


class RequestData(BaseModel):
    object_types: Set[str] = Field(default_factory=set)
    module_id: Optional[int] = None
    include_valids: bool = Field(default=True, description="Search in Objects?")
    include_modules: bool = Field(default=True, description="Search in Module Objects?")
    query: str = Field(min_length=1)

    @field_validator("query")
    def validate_query(cls, value: str) -> str:
        if '"' in value or "\\" in value:
            raise ValueError("Invalid search characters")
        return value

    @model_validator(mode="after")
    def validate_includes(self) -> Self:
        if self.module_id:
            self.include_modules = True
        if not self.include_modules and not self.include_valids:
            raise ValueError("You must include someting")
        return self

    def validate_object_types(self, allowed: Set[str]):
        if not self.object_types:
            self.object_types = allowed
            return

        invalid_object_types: Set[str] = self.object_types - allowed
        if invalid_object_types:
            raise ValueError(f"Allowed Object_Types are: {', '.join(allowed)}")


class SearchObject(BaseModel, Generic[TModel]):
    Module_ID: Optional[int] = None
    Object_Type: str

    Title: str
    Description: str
    Model: TModel

    model_config = ConfigDict(from_attributes=True, title="SearchObject")


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        module_objects_to_models_parser: ModuleObjectsToModelsParser,
        context: SearchEndpointContext,
        request_data: RequestData,
        pagination: SimplePagination,
    ):
        self._session: Session = session
        self._module_objects_to_models_parser: ModuleObjectsToModelsParser = module_objects_to_models_parser
        self._context: SearchEndpointContext = context
        self._request_data: RequestData = request_data
        self._pagination: SimplePagination = pagination

    def handle(self) -> PagedResponse[SearchObject]:
        if self._pagination.limit > 50:
            raise ValueError("Pagination limit is too high")
        self._request_data.validate_object_types(self._context.allowed_object_types)

        paginated: PaginatedQueryResult = query_paginated_no_scalars(
            query=self._build_statement(),
            session=self._session,
            limit=self._pagination.limit,
            offset=self._pagination.offset,
        )

        search_objects: List[SearchObject] = []
        for row in paginated.items:
            parsed_model: BaseModel = self._module_objects_to_models_parser.parse(
                row,
                self._context.model_map,
            )

            description: str = ""
            match getattr(row, "Description", None):
                case str() as row_description:
                    soup = BeautifulSoup(row_description, "html.parser")
                    description = soup.get_text()

            search_object: SearchObject = SearchObject(
                Module_ID=row.Module_ID,
                Object_Type=row.Object_Type,
                Title=row.Title or "",
                Description=description,
                Model=parsed_model,
            )
            search_objects.append(search_object)

        return PagedResponse[SearchObject](
            total=paginated.total_count,
            offset=self._pagination.offset,
            limit=self._pagination.limit,
            results=search_objects,
        )

    def _build_statement(self) -> Select:
        branches: List[Select] = []
        if self._request_data.include_valids:
            branches.append(self._valid_branch())
        if self._request_data.include_modules:
            branches.append(self._module_branch())

        combined = union_all(*branches).subquery() if len(branches) > 1 else branches[0].subquery()

        like_query: str = f"%{self._request_data.query}%"
        return (
            select(combined)
            .where(or_(*[combined.c[name].like(like_query) for name in self._context.search_columns]).self_group())
            .where(combined.c.Object_Type.in_(self._request_data.object_types))
            .order_by(
                desc(combined.c.Modified_Date),
                desc(combined.c.Module_ID),
                asc(combined.c.UUID),
            )
        )

    def _valid_branch(self) -> Select:
        timepoint: datetime = datetime.now(timezone.utc)
        subq = (
            select(
                ObjectsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ObjectsTable)
            .filter(ObjectsTable.Start_Validity <= timepoint)
            .subquery()
        )

        return (
            select(literal(0).label("Module_ID"), *[subq.c[name] for name in self._context.used_columns])
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > timepoint,
                    subq.c.End_Validity.is_(None),
                ).self_group()
            )
        )

    def _module_branch(self) -> Select:
        subq = (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=(ModuleObjectsTable.Module_ID, ModuleObjectsTable.Code),
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable)
            .join(ModuleObjectsTable.ModuleObjectContext)
            .filter(ModuleObjectContextTable.Hidden == False)
        )

        if self._request_data.module_id is not None:
            subq = subq.filter(ModuleObjectsTable.Module_ID == self._request_data.module_id).filter(
                ModuleTable.Closed == False
            )
        else:
            subq = subq.filter(ModuleTable.is_active)

        subq = subq.subquery()

        return (
            select(subq.c.Module_ID, *[subq.c[name] for name in self._context.used_columns])
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Deleted == False)
        )


def get_search_endpoint(
    session: Annotated[Session, Depends(depends_db_session)],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    module_objects_to_models_parser: Annotated[
        ModuleObjectsToModelsParser, Depends(Provide[ApiContainer.module_objects_to_models_parser])
    ],
    context: Annotated[SearchEndpointContext, Depends()],
    request_data: Annotated[RequestData, Body()],
) -> PagedResponse[SearchObject]:
    handler: EndpointHandler = EndpointHandler(
        session,
        module_objects_to_models_parser,
        context,
        request_data,
        pagination,
    )
    results: PagedResponse[SearchObject] = handler.handle()
    return results
