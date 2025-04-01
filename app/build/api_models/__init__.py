"""
Contains hardcoded pydantic models that
    can be used by the fastapi endpoints.
"""

from app.build.objects.types import Model

from app.build.api_models import user


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

