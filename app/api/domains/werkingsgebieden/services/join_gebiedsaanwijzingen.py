from collections.abc import Iterator
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.modules.services.advanced_objects_resolver import (
    AdvancedObjectsResolver,
    AdvancedObjectsResolverFactory,
)
from app.api.domains.modules.types import PublicModuleStatusCode
from app.api.domains.objects.services.gebiedsaanwijzing_service import GebiedsaanwijzingService
from app.core.db.base import Base
from app.core.tables.modules import ModuleStatusHistoryTable
from app.core.utils.utils import DATETIME_MIN


class IncludeModulesConfig(BaseModel):
    module_id: int
    has_user: bool


class JoinGebiedsaanwijzingenConfig(BaseModel):
    from_fields: set[str]
    to_field: str
    to_model: type[BaseModel]
    columns: set[str]
    include_modules: IncludeModulesConfig | None = None


class JoinGebiedsaanwijzingenService:
    def __init__(
        self,
        gebiedsaanwijzingen_service: GebiedsaanwijzingService,
        object_resolver_factory: AdvancedObjectsResolverFactory,
        session: Session,
        config: JoinGebiedsaanwijzingenConfig,
    ):
        self._gebiedsaanwijzingen_service: GebiedsaanwijzingService = gebiedsaanwijzingen_service
        self._object_resolver_factory: AdvancedObjectsResolverFactory = object_resolver_factory
        self._session: Session = session

        self._config: JoinGebiedsaanwijzingenConfig = config
        self._valid_timepoint: datetime = datetime.now(UTC)

    def join_gebiedsaanwijzingen(self, rows: list[BaseModel]) -> list[BaseModel]:
        if not rows:
            return rows
        if len(rows) != 1:
            raise RuntimeError("JoinGebiedsaanwijzingenService should only be used for single results")

        row = rows[0]
        collected_aanwijzing_codes: set[str] = set()

        for field_key in self._config.from_fields:
            field_value: str = getattr(row, field_key)
            fields_aanwijzing_codes: set[str] = self._gebiedsaanwijzingen_service.get_aanwijzing_codes_in_html(
                field_value
            )
            collected_aanwijzing_codes.update(fields_aanwijzing_codes)

        # If we dont have any then we wont need to merge any data back in
        if len(collected_aanwijzing_codes) == 0:
            return rows

        gebieden = self._resolve_codes(collected_aanwijzing_codes)
        setattr(row, self._config.to_field, gebieden)
        rows[0] = row

        return rows

    def _resolve_codes(self, aanwijzing_codes: set[str]) -> list[BaseModel]:
        # If we do not have a user then we should limit how far in the module you can search for data
        # based on the latest public version of the module
        module_timepoint, module_id = self._resolve_module_timepoint()

        gebied_codes: set[str] = set()
        gebiedengroep_codes: set[str] = set()

        gebiedsaanwijzingen = self._get_latests(module_timepoint, module_id, aanwijzing_codes)
        for gebiedsaanwijzing in gebiedsaanwijzingen:
            refs: list[str] = gebiedsaanwijzing.Target_Codes
            for ref in refs:
                object_type, _ = ref.split("-", 1)
                match object_type:
                    case "gebiedengroep":
                        gebiedengroep_codes.add(ref)
                    case "gebied":
                        gebied_codes.add(ref)

        if gebiedengroep_codes:
            gebiedengroepen = self._get_latests(module_timepoint, module_id, gebiedengroep_codes)
            for gebiedengroep in gebiedengroepen:
                refs: list[str] = gebiedengroep.Gebieden
                gebied_codes.update(refs)

        if not gebied_codes:
            return []

        gebieden = self._get_latests(module_timepoint, module_id, gebied_codes)
        gebieden_parsed = [self._config.to_model.model_validate(gebied) for gebied in gebieden]
        return gebieden_parsed

    def _get_latests(self, module_timepoint: datetime, module_id: int | None, codes: set[str]) -> Iterator[Base]:
        resolver: AdvancedObjectsResolver = self._object_resolver_factory.create_service(
            self._session,
            self._config.columns,
            self._valid_timepoint,
            module_timepoint,
            filter_codes=codes,
            filter_module_id=module_id,
        )
        results = resolver.fetch_objects()
        return results

    def _resolve_module_timepoint(self) -> tuple[datetime, int | None]:
        if not self._config.include_modules:
            return DATETIME_MIN, None

        has_user: bool = self._config.include_modules.has_user
        module_id: int = self._config.include_modules.module_id

        # If we have a user then you can watch everything
        # So you can just view the newest version of the module
        if has_user:
            return self._valid_timepoint, module_id

        # Else we need to figure the datetime of the newest public module status
        # And use that ModuleStatus datetime
        stmt = (
            select(ModuleStatusHistoryTable)
            .filter(ModuleStatusHistoryTable.Module_ID == module_id)
            .filter(ModuleStatusHistoryTable.Status.in_(PublicModuleStatusCode.values()))
            .order_by(ModuleStatusHistoryTable.Created_Date.desc())
            .limit(1)
        )
        row = self._session.execute(stmt).scalar_one_or_none()

        # If we do not have a row, than we are not allowed to search for objects in this module
        if not row:
            return DATETIME_MIN, None

        return row.Created_Date, module_id


class JoinGebiedsaanwijzingenServiceFactory:
    def __init__(
        self,
        gebiedsaanwijzingen_service: GebiedsaanwijzingService,
        object_resolver_factory: AdvancedObjectsResolverFactory,
    ):
        self._gebiedsaanwijzingen_service: GebiedsaanwijzingService = gebiedsaanwijzingen_service
        self._object_resolver_factory: AdvancedObjectsResolverFactory = object_resolver_factory

    def create_service(
        self,
        session: Session,
        config: JoinGebiedsaanwijzingenConfig,
    ) -> JoinGebiedsaanwijzingenService:
        return JoinGebiedsaanwijzingenService(
            self._gebiedsaanwijzingen_service,
            self._object_resolver_factory,
            session,
            config,
        )
