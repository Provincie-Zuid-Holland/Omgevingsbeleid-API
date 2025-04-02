from typing import List

import pytest

from app.dynamic.config.models import Model
from app.extensions.lineage_resolvers.endpoints.object_latest import ObjectLatestEndpoint
from app.extensions.lineage_resolvers.endpoints.object_version import ObjectVersionEndpoint
from app.extensions.lineage_resolvers.endpoints.valid_list_lineage_tree import ValidListLineageTreeEndpoint
from app.extensions.lineage_resolvers.endpoints.valid_list_lineages import ValidListLineagesEndpoint
from app.extensions.users.db.tables import UsersTable
from app.tests.fixture_factories.user_factory import UserFixtureFactory
from app.tests.fixtures import MockResponseModel


@pytest.fixture
def endpoint_valid_lineage(mock_converter):
    response_model = Model(id="mock_get", name="AmbitieGet", pydantic_model=MockResponseModel)

    return ValidListLineagesEndpoint(
        converter=mock_converter,
        endpoint_id="test_objects_endpoint",
        path="/ambitie/testpath",
        object_id="ambitie",
        object_type="ambitie",
        response_model=response_model,
        allowed_filter_columns=[],
    )


@pytest.fixture
def endpoint_lineage_tree(mock_converter):
    response_model = Model(id="mock_get", name="AmbitieGet", pydantic_model=MockResponseModel)

    return ValidListLineageTreeEndpoint(
        converter=mock_converter,
        endpoint_id="test_objects_endpoint",
        path="/ambitie/testpath",
        object_id="ambitie",
        object_type="ambitie",
        response_model=response_model,
        allowed_filter_columns=[],
    )


@pytest.fixture
def endpoint_object_latest(mock_converter):
    response_model = Model(id="mock_get", name="AmbitieGet", pydantic_model=MockResponseModel)
    return ObjectLatestEndpoint(
        converter=mock_converter,
        endpoint_id="test_latest_endpoint",
        path="/ambitie/testpath",
        object_id="ambitie",
        object_type="ambitie",
        response_model=response_model,
    )


@pytest.fixture
def endpoint_object_version(mock_converter):
    response_model = Model(id="mock_get", name="AmbitieGet", pydantic_model=MockResponseModel)
    return ObjectVersionEndpoint(
        converter=mock_converter,
        endpoint_id="test_objects_endpoint",
        path="/ambitie/testpath",
        object_id="ambitie",
        object_type="ambitie",
        response_model=response_model,
    )


@pytest.fixture
def populate_users(db) -> List[UsersTable]:
    uf = UserFixtureFactory(db)
    uf.create_all_objects()
    uf.populate_db()
    yield uf.objects
