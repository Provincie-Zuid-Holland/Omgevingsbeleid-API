"""
Contains hardcoded pydantic models that
    can be used by the fastapi endpoints.
"""

from app.build.api_models import user
from app.core.types import Model


DECLARED_MODELS = [
    Model(
        id="user_short",
        name="UserShort",
        pydantic_model=user.UserShort,
    ),
    Model(
        id="user_login_details",
        name="UserLoginDetail",
        pydantic_model=user.UserLoginDetail,
    ),
]

