import uuid
from typing import Annotated, List

from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException
from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails
from sqlalchemy.orm import Session
from starlette import status

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.publications.exceptions import DSOConfigurationException, DSORenvooiException
from app.api.domains.publications.services import PublicationVersionValidator
from app.api.domains.publications.services.act_package import ActPackageBuilderFactory, ActPackageBuilder
from app.api.domains.publications.services.validate_publication_service import ValidatePublicationException
from app.api.domains.publications.types.enums import MutationStrategy, PackageType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.exceptions import LoggedHttpException
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationVersionTable
from app.core.tables.users import UsersTable


class PublicationValidate(BaseModel):
    version_id: uuid.UUID


@inject
def get_validate_act_package_endpoint(
    publication_version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    publication_version_validator: Annotated[
        PublicationVersionValidator, Depends(Provide[ApiContainer.publication.version_validator])
    ],
    _: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_act_package,
            )
        ),
    ],
    package_builder_factory: Annotated[
        ActPackageBuilderFactory, Depends(Provide[ApiContainer.publication.act_package_builder_factory])
    ],
    session: Annotated[Session, Depends(depends_db_session)],
):
    errors: List[ErrorDetails] = publication_version_validator.get_errors(publication_version)
    if len(errors) != 0:
        raise HTTPException(status.HTTP_409_CONFLICT, errors)

    try:
        _: ActPackageBuilder = package_builder_factory.create_builder(
            session,
            publication_version,
            PackageType.VALIDATION,  # because we're validating, this is always VALIDATION type
            MutationStrategy.RENVOOI,
        )
    except HTTPException as e:
        # This is already correctly formatted
        raise e
    except ValidationError as e:
        raise HTTPException(441, e.errors())
    except DSOConfigurationException as e:
        raise LoggedHttpException(status_code=442, detail=e.message) from e
    except DSORenvooiException as e:
        raise LoggedHttpException(status_code=443, detail=e.message, log_message=e.internal_error)
    except ValidatePublicationException as e:
        raise LoggedHttpException(status_code=444, detail=e.dump_errors(), log_message=e.dump_errors())
    except Exception as e:
        # We do not know what to except here
        # This will result in a 500 server error
        raise e

    return ResponseOK(message="OK")
