from typing import Any, List, Optional, Union

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.crud.crud_beleidskeuze import LINK_DESCRIPTION
from app.models.base import MANY_TO_MANY_RELATIONS
from app.util.legacy_helpers import SearchFields


class GraphService:
    """
    Service providing graph representations on generic models
    and their relationships
    """

    LINK_DESCRIPTION = "Koppeling"

    def __init__(self, db: Session, graphable_model_services: List[Any]):
        self.db = db
        self.graphables = graphable_model_services
        self.nodes = list()
        self.links = list()
        self.valid_uuids = list()

    def calculate_relations(self):
        self.nodes, self.valid_uuids = self._populate_valid_nodes()
        self.links = self._populate_links()
        return self._graph_view_response()

    def _graph_view_response(self):
        return {"links": self.links, "nodes": self.nodes}

    def _populate_valid_nodes(self):
        """
        Query each entity defined as graphable for valid items
        and map to node list + valid UUIDs
        """
        node_list = list()
        valid_uuid_list = list()

        for service in self.graphables:
            valid_objects = service.fetch_graph_nodes()

            if len(valid_objects) == 0:
                continue

            mapped_nodes = list(map(self._node_mapper, valid_objects))
            node_list.extend(mapped_nodes)

            # Populate UUIDS
            valid_uuid_list += [obj.UUID for obj in valid_objects]

        return node_list, valid_uuid_list

    def _populate_links(self, valid_uuids: Optional[List[str]] = None):
        """
        Query each Many-to-Many association
        table for matching valid id's.
        Map the results as graphing links.
        """
        if not valid_uuids:
            valid_uuids = self.valid_uuids

        links = list()
        for relation in MANY_TO_MANY_RELATIONS:
            association_objects = (
                self.db.query(relation.model)
                .filter(
                    and_(
                        relation.left.in_(valid_uuids),
                        relation.right.in_(valid_uuids),
                    )
                )
                .all()
            )

            # Map format
            for item in association_objects:
                links.append(
                    {
                        "source": getattr(item, relation.left.key),
                        "target": getattr(item, relation.right.key),
                        "type": LINK_DESCRIPTION,
                    }
                )

        return links

    def _node_mapper(self, valid_object: Any):
        searchable_columns: SearchFields = valid_object.get_search_fields()
        title_field = (getattr(valid_object, searchable_columns.title.key),)
        return {
            "UUID": valid_object.UUID,
            "Titel": title_field[0],
            "Type": valid_object.__tablename__.lower(),
        }
