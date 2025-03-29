from abc import ABC, abstractmethod
from pydantic import BaseModel


class EndpointContextBuilderData(BaseModel):
    endpoint_id: str
    path: str


class BaseEndpointContext(BaseModel):
    builder_data: EndpointContextBuilderData

