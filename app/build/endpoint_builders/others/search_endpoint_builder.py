from typing import Dict, Set, Union

from pydantic import BaseModel

from app.api.domains.others.endpoints.search_endpoint import SearchEndpointContext, SearchObject, get_search_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.build.services.model_dynamic_type_builder import ModelDynamicTypeBuilder
from app.core.services.models_provider import ModelsProvider
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.objects import ObjectsTable
from app.core.types import DynamicObjectModel, Model


class SearchEndpointBuilder(EndpointBuilder):
    def __init__(self, model_dynamic_type_builder: ModelDynamicTypeBuilder):
        self._model_dynamic_type_builder: ModelDynamicTypeBuilder = model_dynamic_type_builder

    def get_id(self) -> str:
        return "search"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data

        search_columns: Set[str] = set(resolver_config["search_columns"])
        model_map: Dict[str, str] = resolver_config["model_map"]
        response_model_name: str = resolver_config["response_model_name"]
        used_columns: Set[str] = self._compute_used_columns(
            set(model_map.values()),
            models_provider,
            search_columns,
        )

        context = SearchEndpointContext(
            builder_data=builder_data,
            model_map=model_map,
            allowed_object_types=set(model_map.keys()),
            search_columns=search_columns,
            used_columns=used_columns,
        )
        endpoint = self._inject_context(get_search_endpoint, context)

        union_object_type: Union[BaseModel] = self._model_dynamic_type_builder.build_object_union_type(model_map)
        response_type = PagedResponse[SearchObject[union_object_type]]
        response_type.__name__ = response_model_name

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=response_type,
            summary="Search for objects",
            description=None,
            tags=["Search"],
        )

    def _compute_used_columns(
        self, model_ids: Set[str], models_provider: ModelsProvider, search_columns: Set[str]
    ) -> Set[str]:
        # We calculate the shared and used columns at build time
        # In general, we need a shared columns set (used by both tables)
        # to make the UNION query valid
        objects_set: Set[str] = set([c.name for c in ObjectsTable.__table__.columns])
        module_set: Set[str] = set([c.name for c in ModuleObjectsTable.__table__.columns])
        all_shared_columns: Set[str] = objects_set.intersection(module_set)

        # And now that we are working on this, lets make the column set smaller
        # By only requesting columns that will be used by the models
        requested_columns: Set[str] = set()
        for model_id in model_ids:
            model: Union[Model, DynamicObjectModel] = models_provider.get_model(model_id)
            if not isinstance(model, DynamicObjectModel):
                raise RuntimeError(f"Model with id '{model_id}' is not a dynamic object model and cant be used here")
            for column in model.columns:
                if column.static:
                    continue
                requested_columns.add(column.name)

        invalid_requested_columns: Set[str] = requested_columns - all_shared_columns
        if invalid_requested_columns:
            raise RuntimeError(
                f"Invalid requested columns ({', '.join(invalid_requested_columns)}) which do not exists in both tables"
            )

        # These are used to filter on, so must also be fetched in the inner query
        invalid_search_columns: Set[str] = search_columns - all_shared_columns
        if invalid_search_columns:
            raise RuntimeError(
                f"Invalid search columns ({', '.join(invalid_search_columns)}) which do not exists in both tables"
            )

        final_columns: Set[str] = requested_columns
        final_columns.update(
            # These are used by the search endpoints code
            ["UUID", "Modified_Date", "Object_Type", "Title", "Description"]
        )
        final_columns.update(search_columns)

        return final_columns
