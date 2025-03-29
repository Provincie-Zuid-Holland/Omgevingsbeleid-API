import functools
import inspect
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from app.api.api_container import ApiContainer
from app.api.domains.objects.endpoints.object_latest_endpoint import ObjectLatestEndpointContext, view_endpoint, view_endpoint2
from app.build.build_container import BuilderContainer
from app.build.api_builder import ApiBuilder
from app.build.endpoint_builders.objects.object_latest_endpoint_builder import AmbitieFull, ObjectLatestEndpointBuilder
import asyncio  # noqa


endpoints = []


def build_endpoints():
    data = {
        "response_type": AmbitieFull,
        "builder_data": {
            "endpoint_id": "object_latest",
            "path": "/ambitie/{lineage_id}/object-latest",
        }
    }
    context = ObjectLatestEndpointContext.model_validate(data)
    endpoint = view_endpoint(context)

    # container = BuilderContainer()
    # container.wire(modules=["app.build.api_builder"])

    # api_builder = ApiBuilder()
    # api_builder.build()


    # endpoint partial fill hopefully

    partial_func = functools.partial(view_endpoint2, context=context)
    functools.update_wrapper(partial_func, view_endpoint2)
    # Adjust the signature to remove the "context" parameter.
    original_sig = inspect.signature(view_endpoint2)
    new_params = [
        param for name, param in original_sig.parameters.items()
        if name != "context"
    ]
    new_sig = original_sig.replace(parameters=new_params)
    partial_func.__signature__ = new_sig
    
    return [{
        "path": "/ambitie/{lineage_id}/object-latest",
        "endpoint": endpoint,
        "methods": ["GET"],
        "response_class": JSONResponse,
        "summary": f"View latest valid record for an Ambitie lineage id",
    }, {
        "path": "/beleidskeuze/{lineage_id}/object-latest",
        "endpoint": partial_func,
        "methods": ["GET"],
        "response_class": JSONResponse,
        "summary": f"View latest valid record for an Beleidskeuze lineage id",
    }]


endpoints = build_endpoints()




container = ApiContainer()
container.wire(modules=[__name__])




app = FastAPI()

router = APIRouter()


# router.add_api_route(
#     "/ambitie/{lineage_id}/object-latest",
#     endpoint,
#     methods=["GET"],
#     response_class=JSONResponse,
#     summary=f"View latest valid record for an Ambitie lineage id",
# )

# router.add_api_route(
#     "/beleidskeuze/{lineage_id}/object-latest",
#     partial_func,
#     methods=["GET"],
#     response_class=JSONResponse,
#     summary=f"View latest valid record for an Beleidskeuze lineage id",
# )

for endpoint in endpoints:
    router.add_api_route(
        endpoint["path"],
        endpoint["endpoint"],
        methods=endpoint["methods"],
        response_class=endpoint["response_class"],
        summary=endpoint["summary"],
    )


app.include_router(router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Omgevingsdienst API",
        version="1.0.0",
        openapi_version="3.1.0",
        description="Omgevingsdienst API",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": "https://avatars.githubusercontent.com/u/60095455?s=200&v=4"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


a = True
