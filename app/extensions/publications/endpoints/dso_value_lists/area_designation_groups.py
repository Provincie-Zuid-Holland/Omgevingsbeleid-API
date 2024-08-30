from enum import Enum
from typing import List

from dso.services.ow.imow_waardelijsten import TypeGebiedsaanwijzingEnum as AreaDesignationTypes
from dso.services.ow.imow_waardelijsten import get_groep_options_for_gebiedsaanwijzing_type
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver

AreaDesignationTypeEnum = Enum("AreaDesignationTypeEnum", {member.name: member.name for member in AreaDesignationTypes})


class AreaDesignationValueList(BaseModel):
    Allowed_Values: List[str]


class ListAreaDesignationGroupsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(type: AreaDesignationTypeEnum) -> AreaDesignationValueList:  # type: ignore
            enum_member = AreaDesignationTypes[type.name]
            group_options = get_groep_options_for_gebiedsaanwijzing_type(enum_member)
            if group_options is None:
                raise HTTPException(
                    status_code=403,
                    detail=f"Group options not found for area designation type {type.name}",
                )
            return AreaDesignationValueList(Allowed_Values=group_options)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=AreaDesignationValueList,
            summary="List the allowed groups to use for this publication document_type",
            description=None,
            tags=["Publication Value Lists"],
        )

        return router


class ListAreaDesignationGroupsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_area_designation_groups"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListAreaDesignationGroupsEndpoint(path)
