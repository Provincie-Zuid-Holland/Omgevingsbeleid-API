from typing import List

from dso.services.ow.waardelijsten import GEBIEDSAANWIJZING_TO_GROEP_MAPPING
from dso.services.ow.waardelijsten import TYPE_GEBIEDSAANWIJZING_VALUES as AreaDesignationTypes
from dso.services.ow.waardelijsten.models import ValueEntry
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver


class AreaDesignationValueList(BaseModel):
    Allowed_Values: List[ValueEntry]


class ListAreaDesignationGroupsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(gba_type: str) -> AreaDesignationValueList:
            # allow lookup using either term, label, or full URI for easier use
            valid_terms = {entry.term: entry for entry in AreaDesignationTypes.waarden.waarde}
            valid_labels = {entry.label: entry for entry in AreaDesignationTypes.waarden.waarde}
            valid_uris = {entry.uri: entry for entry in AreaDesignationTypes.waarden.waarde}

            type_entry = valid_terms.get(gba_type) or valid_labels.get(gba_type) or valid_uris.get(gba_type)

            if not type_entry:
                valid_options = (
                    f"Terms: {', '.join(valid_terms.keys())}\n"
                    f"Labels: {', '.join(valid_labels.keys())}\n"
                    f"URIs: {', '.join(valid_uris.keys())}"
                )
                raise HTTPException(
                    status_code=400, detail=f"Invalid area designation type. Must be one of:\n{valid_options}"
                )

            groep_value_list = GEBIEDSAANWIJZING_TO_GROEP_MAPPING.get(type_entry.uri)
            if not groep_value_list:
                raise HTTPException(
                    status_code=403,
                    detail=f"Group options not found for area designation type {gba_type}",
                )

            return AreaDesignationValueList(Allowed_Values=groep_value_list.waarden.waarde)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=AreaDesignationValueList,
            summary="List the allowed groups to use for this publication document_type",
            description="Accepts either term, label, or full URI as input to identify the area designation type",
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
