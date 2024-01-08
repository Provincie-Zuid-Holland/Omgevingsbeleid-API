from app.dynamic.config.models import ExtensionModel
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.hierarchy.models import HierarchyStatics


class HierarchyExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="hierarchy_statics",
                name="HierarchyStatics",
                pydantic_model=HierarchyStatics,
            )
        )
