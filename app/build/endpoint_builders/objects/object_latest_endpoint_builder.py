from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from functools import partial

from app.api.domains.objects.endpoints.object_latest_endpoint import ObjectLatestEndpointContext, view_endpoint
from app.build.endpoint_builders.endpoint_builder import EndpointBuilder


class AmbitieFull(BaseModel):
    Object_ID: int
    Object_Type: str
    Code: str
    UUID: str
    Title: str


class BeleidskeuzeFull(BaseModel):
    Object_ID: int
    Object_Type: str
    Code: str
    UUID: str
    Title: str


class ObjectLatestEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_latest"

    def bind_endpoint(
        self,
        # models_resolver: ModelsResolver,
        # endpoint_config: EndpointConfig,
        # api: Api,
        router: APIRouter,
    ):
        data = {
            "response_type": AmbitieFull,
            # "builder_data": {
            #     "endpoint_id": "object_latest",
            #     "path": "/ambitie/{lineage_id}/object-latest",
            # }
        }
        # resolver_config: dict = endpoint_config.resolver_data
        # path: str = endpoint_config.prefix + resolver_config.get("path", "")
        
        context = ObjectLatestEndpointContext.model_validate(data)
        endpoint = view_endpoint(context)

        a = True

        router.add_api_route(
            "/ambitie/{lineage_id}/object-latest",
            endpoint,
            methods=["GET"],
            response_class=JSONResponse,
            summary=f"View latest valid record for an Ambitie lineage id",
        )
