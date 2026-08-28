from typing import Annotated

from fastapi import Depends

from app.api.domains.others.dependencies import depends_hoofdlijn
from app.api.domains.others.types import Hoofdlijn
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.others import HoofdlijnTable
from app.core.tables.users import UsersTable


def get_hoofdlijnen_detail_endpoint(
    _: Annotated[UsersTable, Depends(depends_current_user)],
    hoofdlijn: Annotated[HoofdlijnTable, Depends(depends_hoofdlijn)],
) -> Hoofdlijn:
    result: Hoofdlijn = Hoofdlijn.model_validate(hoofdlijn)
    return result
