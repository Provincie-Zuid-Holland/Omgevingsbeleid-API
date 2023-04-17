from fastapi import APIRouter, Depends, HTTPException
import pydantic

from app.core.security import verify_password
from app.dynamic.utils.response import ResponseOK
from app.dynamic.endpoints.endpoint import Endpoint
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.repository.user_repository import UserRepository
from app.extensions.users.dependencies import (
    depends_current_active_user,
    depends_user_repository,
)


class PasswordUpdate(pydantic.BaseModel):
    password: str
    new_password: str


class PasswordResetEndpoint(Endpoint):
    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            password_in: PasswordUpdate = Depends(),
            current_user: UsersTable = Depends(depends_current_active_user),
            user_repository: UserRepository = Depends(depends_user_repository),
        ) -> ResponseOK:
            return self._handler(user_repository, current_user, password_in)

        router.add_api_route(
            "/password-reset",
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Changes password for a user",
            description=None,
            tags=["Auth"],
        )

        return router

    def _handler(
        self,
        user_repository: UserRepository,
        current_user: UsersTable,
        password_in: PasswordUpdate,
    ):
        valid: bool = verify_password(password_in.password, current_user.Wachtwoord)
        if not valid:
            raise HTTPException(status_code=401, detail="Incorrect password")

        user_repository.change_password(current_user, password_in.new_password)

        return ResponseOK(
            message="OK",
        )
