from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.api.api_general.api import api_router as api_router_general
from app.api.api_v01.api import api_router as api_router_v01
from app.core.config import settings
from app.util.legacy_helpers import parse_filter_str

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V01_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# @app.middleware("http")
# async def legacy_filter_conversion(request: Request, call_next):
#     """
#     Temp workaround to preprocess legacy api filter strings
#     """
#     response = await call_next(request)

#     qp_keys = request.query_params.keys()
    
#     if "all_filters" in qp_keys:
#         for (key, value) in parse_filter_str(request.query_params["all_filters"]).items():
#             response.headers[f"X-All-Filters-{key}"] = value
    
#     if "any_filters" in qp_keys:
#         for (key, value) in parse_filter_str(request.query_params["any_filters"]).items():
#             response.headers[f"X-Any-Filters-{key}"] = value

#     return response

app.include_router(api_router_general)
app.include_router(api_router_v01, prefix=settings.API_V01_STR)
