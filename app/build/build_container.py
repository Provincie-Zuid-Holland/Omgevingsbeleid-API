from dependency_injector import containers, providers

from app.build import api_builder
from app.build.services import config_parser, object_intermediate_builder, validator_provider, object_models_builder
import app.build.services.validators.validators as validators


class BuildContainer(containers.DeclarativeContainer):
    settings = providers.Dependency()
    db = providers.Dependency()

    validator_provider = providers.Singleton(
        validator_provider.ValidatorProvider,
        validators=providers.List(
            providers.Factory(validators.NoneToDefaultValueValidator),
            providers.Factory(validators.LengthValidator),
            providers.Factory(validators.PlainTextValidator),
            providers.Factory(validators.FilenameValidator),
            providers.Factory(validators.HtmlValidator),
            providers.Factory(validators.ImageValidator),
            providers.Factory(validators.NotEqualRootValidator),
            providers.Factory(validators.ObjectCodeExistsValidator),
            providers.Factory(validators.ObjectCodeAllowedTypeValidator),
            providers.Factory(validators.ObjectCodesExistsValidator),
            providers.Factory(validators.ObjectCodesAllowedTypeValidator),
        ),
    )

    object_intermediate_builder = providers.Factory(
        object_intermediate_builder.ObjectIntermediateBuilder,
        validator_provider=validator_provider,
    )
    object_models_builder = providers.Factory(
        object_models_builder.ObjectModelsBuilder,
        validator_provider=validator_provider,
    )
    config_parser = providers.Factory(
        config_parser.ConfigParser,
        object_intermediate_builder=object_intermediate_builder,
        object_models_builder=object_models_builder,
    )

    api_builder = providers.Factory(
        api_builder.ApiBuilder,
        settings=settings,
        db=db,
        config_parser=config_parser,
    )
