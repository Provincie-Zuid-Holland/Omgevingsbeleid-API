from datetime import timedelta
from typing import Optional, Type

import pydantic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token
from app.core.settings import settings
from app.dynamic.config.models import Model
from app.dynamic.endpoints.endpoint import Endpoint
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_user_repository
from app.extensions.users.model import User
from app.extensions.users.repository.user_repository import UserRepository


class LoginAccessTokenEndpoint(Endpoint):
    def __init__(self, models_resolver: ModelsResolver):
        response_model: Model = models_resolver.get("auth_token")
        self._response_type: Type[pydantic.BaseModel] = response_model.pydantic_model

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            form_data: OAuth2PasswordRequestForm = Depends(),
            user_repository: UserRepository = Depends(depends_user_repository),
        ) -> self._response_type:
            return self._handler(user_repository, form_data)

        router.add_api_route(
            "/login/access-token",
            fastapi_handler,
            methods=["POST"],
            response_model=self._response_type,
            summary=f"Login an user and receive a JWT token",
            description=None,
            tags=["Auth"],
        )

        return router

    def _handler(self, user_repository: UserRepository, form_data: OAuth2PasswordRequestForm):
        user: Optional[UsersTable] = user_repository.authenticate(form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        elif not user.IsActief:
            raise HTTPException(status_code=401, detail="Inactive user")

        access_token = create_access_token(user.UUID)

        pydantic_user: User = User.from_orm(user)

        response = self._response_type.parse_obj(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "identifier": pydantic_user,
            }
        )

        return response
