from typing import Any, List

from devtools import debug
from sqlalchemy import or_, and_
from sqlalchemy.orm import Query, Session, Session, aliased
from sqlalchemy_utils import QueryChain

from app import crud, models, schemas
from app.db.base_class import Base
from app.db.session import SessionLocal
from app.models.base import MANY_TO_MANY_RELATIONS
from app.util.legacy_helpers import SearchFields


GRAPHABLES: List[Any] = [
    (models.Ambitie, crud.ambitie, schemas.Ambitie),
    (models.Beleidskeuze, crud.beleidskeuze, schemas.Beleidskeuze),
    (models.Belang, crud.belang, schemas.Belang),
    (models.Beleidsregel, crud.beleidsregel, schemas.Beleidsregel),
    (models.Beleidsdoel, crud.beleidsdoel, schemas.Beleidsdoel),
    (models.Beleidsprestatie, crud.beleidsprestatie, schemas.beleidsprestatie),
    (models.Maatregel, crud.maatregel, schemas.Maatregel),
    (models.Thema, crud.thema, schemas.Thema),
    (models.Verordening, crud.verordening, schemas.Verordening),
]


class GraphService:
    """
    Service providing graph representations on generic models
    and their relationships
    """

    def __init__(self):
        self.db: Session = SessionLocal()
        self.graphables = GRAPHABLES
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
        for entity, service, schema in self.graphables:
            if entity is models.Verordening:
                valid_objects = service.valid_without_lid_type()
            else:
                valid_objects = service.valid(limit=-1)

            if len(valid_objects) is 0:
                continue

            mapped_nodes = list(map(self._node_mapper, valid_objects))
            node_list.extend(mapped_nodes)

            # Populate UUIDS
            valid_uuid_list += [obj.UUID for obj in valid_objects]

        return node_list, valid_uuid_list

    def _populate_links(self):
        """
        Query each Many-to-Many association
        table for matching valid id's.
        Map the results as graphing links.
        """
        links = list()
        for relation in MANY_TO_MANY_RELATIONS:
            association_objects = (
                self.db.query(relation.model)
                .filter(
                    and_(
                        relation.left.in_(self.valid_uuids),
                        relation.right.in_(self.valid_uuids),
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
                        "type": "Koppeling",
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

    # TODO: fix
    def _add_special_relations(self):
        """
        Relationships that dont fit the generic models
        """
        # Beleidsrelaties
        br_manager = Beleidsrelaties_Schema.Meta.manager(Beleidsrelaties_Schema)
        brs = br_manager.get_all(True)

        for br in brs:

            links.append(
                {
                    "source": br["Van_Beleidskeuze"]["UUID"],
                    "target": br["Naar_Beleidskeuze"]["UUID"],
                    "type": "Relatie",
                }
            )

        valid_links = []
        for link in links:
            if link["target"] in valid_uuids and link["source"] in valid_uuids:
                valid_links.append(link)

        pass


graph_service = GraphService()
