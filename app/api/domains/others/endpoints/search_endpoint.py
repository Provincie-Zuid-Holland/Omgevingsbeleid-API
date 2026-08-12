from datetime import UTC, datetime
from typing import Annotated, Self

from bs4 import BeautifulSoup
from dependency_injector.wiring import Provide
from fastapi import Body, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import Select, asc, desc, func, literal, or_, select, union_all
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.modules.services.module_objects_to_models_parser import ModuleObjectsToModelsParser
from app.api.domains.modules.types import PublicModuleStatusCode
from app.api.domains.users.dependencies import depends_optional_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import (
    PagedResponse,
    PaginatedQueryResult,
    SimplePagination,
    query_paginated_no_scalars,
)
from app.core.tables.modules import (
    ModuleObjectContextTable,
    ModuleObjectsTable,
    ModuleStatusHistoryTable,
    ModuleTable,
)
from app.core.tables.objects import ObjectsTable
from app.core.tables.users import UsersTable


class SearchEndpointContext(BaseEndpointContext):
    model_map: dict[str, str]
    allowed_object_types: set[str]
    search_columns: set[str]
    used_columns: set[str]


class RequestData(BaseModel):
    object_types: set[str] = Field(default_factory=set)
    module_id: int | None = None
    include_valids: bool = Field(default=True, description="Search in Objects?")
    include_modules: bool = Field(default=True, description="Search in Module Objects?")
    query: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_includes(self) -> Self:
        if self.module_id:
            self.include_modules = True
        if not self.include_modules and not self.include_valids:
            raise ValueError("You must include something")
        return self

    def validate_object_types(self, allowed: set[str]):
        if not self.object_types:
            self.object_types = allowed
            return

        invalid_object_types: set[str] = self.object_types - allowed
        if invalid_object_types:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Allowed Object_Types are: {', '.join(sorted(allowed))}",
            )


class SearchObject[T: BaseModel](BaseModel):
    Module_ID: int | None = None
    Object_Type: str

    Title: str
    Description: str
    Model: T

    model_config = ConfigDict(from_attributes=True, title="SearchObject")


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        module_objects_to_models_parser: ModuleObjectsToModelsParser,
        user: UsersTable | None,
        context: SearchEndpointContext,
        request_data: RequestData,
        pagination: SimplePagination,
    ):
        self._session: Session = session
        self._module_objects_to_models_parser: ModuleObjectsToModelsParser = module_objects_to_models_parser
        self._user: UsersTable | None = user
        self._context: SearchEndpointContext = context
        self._request_data: RequestData = request_data
        self._pagination: SimplePagination = pagination

    def handle(self) -> PagedResponse[SearchObject]:
        if self._pagination.limit > 50:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Pagination limit is too high")
        self._request_data.validate_object_types(self._context.allowed_object_types)

        paginated: PaginatedQueryResult = query_paginated_no_scalars(
            query=self._build_statement(),
            session=self._session,
            limit=self._pagination.limit,
            offset=self._pagination.offset,
        )

        search_objects: list[SearchObject] = []
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
                Module_ID=row.Module_ID or None,
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
        branches: list[Select] = []
        if self._request_data.include_valids:
            branches.append(self._valid_branch())
        if self._request_data.include_modules:
            branches.append(self._module_branch())

        combined = union_all(*branches).subquery() if len(branches) > 1 else branches[0].subquery()

        return select(combined).order_by(
            desc(combined.c.Modified_Date),
            desc(combined.c.Module_ID),
            asc(combined.c.UUID),
        )

    def _valid_branch(self) -> Select:
        timepoint: datetime = datetime.now(UTC)
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
            .filter(
                or_(
                    *[subq.c[name].like(self._request_data.query) for name in self._context.search_columns]
                ).self_group()
            )
            .filter(subq.c.Object_Type.in_(self._request_data.object_types))
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

        # If you are not logged in then you are only allowed to view public versions of the module objects
        if not self._user:
            public_status_subq = (
                select(
                    ModuleStatusHistoryTable.Module_ID,
                    ModuleStatusHistoryTable.Created_Date,
                    func.row_number()
                    .over(
                        partition_by=ModuleStatusHistoryTable.Module_ID,
                        order_by=desc(ModuleStatusHistoryTable.ID),
                    )
                    .label("_StatusRowNumber"),
                )
                .filter(ModuleStatusHistoryTable.Status.in_(PublicModuleStatusCode.values()))
                .subquery("public_status_subq")
            )
            subq = (
                subq.join(public_status_subq, ModuleObjectsTable.Module_ID == public_status_subq.c.Module_ID)
                .filter(public_status_subq.c._StatusRowNumber == 1)
                .filter(ModuleObjectsTable.Modified_Date <= public_status_subq.c.Created_Date)
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
            .filter(
                or_(
                    *[subq.c[name].like(self._request_data.query) for name in self._context.search_columns]
                ).self_group()
            )
            .filter(subq.c.Object_Type.in_(self._request_data.object_types))
        )


def get_search_endpoint(
    session: Annotated[Session, Depends(depends_db_session)],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    module_objects_to_models_parser: Annotated[
        ModuleObjectsToModelsParser, Depends(Provide[ApiContainer.module_objects_to_models_parser])
    ],
    user: Annotated[UsersTable | None, Depends(depends_optional_current_user)],
    context: Annotated[SearchEndpointContext, Depends()],
    request_data: Annotated[RequestData, Body()],
) -> PagedResponse[SearchObject]:
    handler: EndpointHandler = EndpointHandler(
        session,
        module_objects_to_models_parser,
        user,
        context,
        request_data,
        pagination,
    )
    results: PagedResponse[SearchObject] = handler.handle()
    return results
