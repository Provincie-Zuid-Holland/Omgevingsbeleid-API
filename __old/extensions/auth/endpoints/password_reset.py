import pydantic
from fastapi import APIRouter, Depends, HTTPException

from app.core_old.dependencies import depends_security
from app.core_old.security import Security
from app.dynamic.endpoints.endpoint import Endpoint
from app.dynamic.utils.response import ResponseOK
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user, depends_user_repository
from app.extensions.users.repository.user_repository import UserRepository


class PasswordUpdate(pydantic.BaseModel):
    password: str
    new_password: str


class PasswordResetEndpoint(Endpoint):
    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            password_in: PasswordUpdate = Depends(),
            current_user: UsersTable = Depends(depends_current_active_user),
            user_repository: UserRepository = Depends(depends_user_repository),
            security: Security = Depends(depends_security),
        ) -> ResponseOK:
            return self._handler(security, user_repository, current_user, password_in)

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
        security: Security,
        user_repository: UserRepository,
        current_user: UsersTable,
        password_in: PasswordUpdate,
    ):
        valid: bool = security.verify_password(password_in.password, current_user.Wachtwoord)
        if not valid:
            raise HTTPException(status_code=401, detail="Incorrect password")

        user_repository.change_password(current_user, password_in.new_password)

        return ResponseOK(
            message="OK",
        )
