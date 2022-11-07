from typing import List

from pydantic import BaseModel


class LinkItem(BaseModel):
    source: str
    target: str
    type: str


class NodeItem(BaseModel):
    Titel: str
    Type: str
    UUID: str


class GraphView(BaseModel):
    links: List[LinkItem] = []
    nodes: List[NodeItem] = []
