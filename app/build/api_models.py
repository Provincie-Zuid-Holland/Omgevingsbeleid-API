"""
Contains hardcoded pydantic models that
    can be used by the fastapi endpoints.
"""

import app.api.domains.users.types as users
import app.api.domains.objects.types as objects
import app.api.domains.others.types as others
import app.api.domains.werkingsgebieden.types as werkingsgebieden
from app.core.types import Model


DECLARED_MODELS = [
    Model(
        id="user_short",
        name="UserShort",
        pydantic_model=users.UserShort,
    ),
    Model(
        id="user_login_details",
        name="UserLoginDetail",
        pydantic_model=users.UserLoginDetail,
    ),
    Model(
        id="area_basic",
        name="AreaBasic",
        pydantic_model=werkingsgebieden.AreaBasic,
    ),
    Model(
        id="werkingsgebied_statics",
        name="WerkingsgebiedStatics",
        pydantic_model=werkingsgebieden.WerkingsgebiedStatics,
    ),
    Model(
        id="hierarchy_statics",
        name="HierarchyStatics",
        pydantic_model=objects.HierarchyStatics,
    ),
    Model(
        id="storage_file_basic",
        name="StorageFileBasic",
        pydantic_model=others.StorageFileBasic,
    ),
    Model(
        id="read_relation_short",
        name="ReadRelationShort",
        pydantic_model=objects.ReadRelationShort,
    ),
    Model(
        id="read_relation",
        name="ReadRelation",
        pydantic_model=objects.ReadRelation,
    ),
    Model(
        id="write_relation",
        name="WriteRelation",
        pydantic_model=objects.WriteRelation,
    ),
]
