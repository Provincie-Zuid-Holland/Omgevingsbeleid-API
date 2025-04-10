from dependency_injector import containers, providers

import app.api.services as api_services
from app.build import api_builder
import app.build.endpoint_builders.objects as endpoint_builders_objects
from app.build.endpoint_builders import endpoint_builder_provider
from app.build.services import config_parser, object_intermediate_builder, tables_builder, validator_provider, object_models_builder
import app.build.services.validators.validators as validators
from app.core.db.session import create_db_engine, init_db_session
from app.core.services.models_provider import ModelsProvider
from app.core.services.event import event_manager
from app.core.settings import Settings
from sqlalchemy.orm import sessionmaker
from app.build.events import create_model_event_listeners, generate_table_event_listeners


class BuildContainer(containers.DeclarativeContainer):
    config = providers.Configuration(pydantic_settings=[Settings()])

    db_engine = providers.Singleton(
        create_db_engine,
        uri=config.SQLALCHEMY_DATABASE_URI,
        echo=config.SQLALCHEMY_ECHO,
    )
    db_session_factory = providers.Singleton(sessionmaker, bind=db_engine, autocommit=False, autoflush=False)
    db = providers.Resource(
        init_db_session,
        session_factory=db_session_factory,
    )

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

    build_event_listeners = providers.Factory(
        event_manager.EventListeners,
        listeners=providers.List(
            # GenerateTableEvent
            providers.Factory(generate_table_event_listeners.AddObjectCodeRelationshipListener),
            providers.Factory(generate_table_event_listeners.AddAreasRelationshipListener),
            providers.Factory(generate_table_event_listeners.AddUserRelationshipListener),
            providers.Factory(generate_table_event_listeners.AddWerkingsgebiedenRelationshipListener),
            providers.Factory(generate_table_event_listeners.AddStoreageFileRelationshipListener),
            # CreateModelEvent
            providers.Factory(create_model_event_listeners.ObjectsExtenderListener),
            providers.Factory(create_model_event_listeners.ObjectStaticsExtenderListener),
            providers.Factory(create_model_event_listeners.AddRelationsListener),
            providers.Factory(create_model_event_listeners.JoinWerkingsgebiedenListener),
        ),
    )
    build_event_manager = providers.Singleton(
        event_manager.EventManager,
        db=db,
        event_listeners=build_event_listeners,
    )

    permission_service = providers.Singleton(api_services.PermissionService)

    endpoint_builder_provider = providers.Singleton(
        endpoint_builder_provider.EndpointBuilderProvider,
        endpoint_builders=providers.List(
            # Objects domain
            providers.Factory(endpoint_builders_objects.ObjectLatestEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectVersionEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectCountsEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectListValidLineagesEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectListValidLineageTreeEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectListAllLatestEndpointBuilder),
            providers.Factory(endpoint_builders_objects.EditObjectStaticEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AtemporalCreateObjectEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AtemporalEditObjectEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AtemporalDeleteObjectEndpointBuilder),
        )
    )

    object_intermediate_builder = providers.Factory(
        object_intermediate_builder.ObjectIntermediateBuilder,
        validator_provider=validator_provider,
    )
    object_models_builder = providers.Factory(
        object_models_builder.ObjectModelsBuilder,
        validator_provider=validator_provider,
        event_manager=build_event_manager,
    )
    config_parser = providers.Factory(
        config_parser.ConfigParser,
        main_config_path=config.MAIN_CONFIG_FILE,
        object_config_path=config.OBJECT_CONFIG_PATH,
        object_intermediate_builder=object_intermediate_builder,
    )

    tables_builder = providers.Factory(
        tables_builder.TablesBuilder,
        event_manager=build_event_manager,
    )

    models_provider = providers.Singleton(ModelsProvider)

    api_builder = providers.Factory(
        api_builder.ApiBuilder,
        db=db,
        config_parser=config_parser,
        object_models_builder=object_models_builder,
        tables_builder=tables_builder,
        endpoint_builder_provider=endpoint_builder_provider,
        models_provider=models_provider,
        permission_service=permission_service,
    )
