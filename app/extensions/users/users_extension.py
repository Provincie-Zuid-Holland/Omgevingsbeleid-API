from uuid import UUID

import pydantic

from app.dynamic.extension import Extension
from app.dynamic.config.models import ExtensionModel
from app.dynamic.models_resolver import ModelsResolver


class UsersExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="gebruikers_short",
                name="GebruikersShort",
                pydantic_model=pydantic.create_model(
                    "GebruikersShort",
                    **{
                        "UUID": (UUID, pydantic.Field()),
                        "Rol": (str, pydantic.Field()),
                        "Gebruikersnaam": (str, pydantic.Field()),
                    },
                ),
            ),
        )
