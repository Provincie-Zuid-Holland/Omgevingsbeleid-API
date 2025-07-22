

from typing import Optional
import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository


class UpgradePlan(BaseModel):
    module_id: int
    input_geo_werkingsgebied_uuid: uuid.UUID



class SelectInputGeoWerkingsgebiedService:
    def __init__(
        self,
        session: Session,
        module_object_repository: ModuleObjectRepository,
        module_id: int,
        igw_uuid: uuid.UUID,
    ):
        pass
    
    def plan(self) -> Optional[UpgradePlan]:

        pass



class SelectInputGeoWerkingsgebiedFactory:
    def __init__(
        self,
        module_object_repository: ModuleObjectRepository,
    ):
        self._module_object_repository: ModuleObjectRepository = module_object_repository

    def create_service(
        self,
        session: Session,
        module_id: int,
        igw_uuid: uuid.UUID,
    ) -> SelectInputGeoWerkingsgebiedService:
        return SelectInputGeoWerkingsgebiedService(
            session,
            self._module_object_repository,
            module_id,
            igw_uuid,
        )

