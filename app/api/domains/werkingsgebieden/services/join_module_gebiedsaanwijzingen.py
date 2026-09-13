from collections.abc import Iterator
from datetime import UTC, datetime

from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.advanced_objects_resolver import (
    AdvancedObjectsResolver,
    AdvancedObjectsResolverFactory,
)
from app.core.db.base import Base


class JoinModuleObjectGebiedsaanwijzingenConfig(BaseModel):
    from_fields: set[str]
    to_field: str
    to_model: type[BaseModel]
    columns: set[str]
    module_id: int
    has_user: bool


def _get_aanwijzing_codes(html: str) -> set[str]:
    result: set[str] = set()

    try:
        soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
        for aanwijzing_html in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
            aanwijzing_code: str = str(aanwijzing_html.get("data-code", ""))
            if not aanwijzing_code:
                continue
            result.add(aanwijzing_code)
    except TypeError:
        pass

    return result


class JoinModuleObjectGebiedsaanwijzingenService:
    def __init__(
        self,
        session: Session,
        object_resolver_factory: AdvancedObjectsResolverFactory,
        config: JoinModuleObjectGebiedsaanwijzingenConfig,
    ):
        self._session: Session = session
        self._object_resolver_factory: AdvancedObjectsResolverFactory = object_resolver_factory

        self._config: JoinModuleObjectGebiedsaanwijzingenConfig = config
        self._valid_timepoint: datetime = datetime.now(UTC)

    def join_gebiedsaanwijzingen(self, rows: list[BaseModel]) -> list[BaseModel]:
        if not rows:
            return rows
        if len(rows) != 1:
            raise RuntimeError("JoinModuleObjectGebiedsaanwijzingenService should only be used for single results")

        row = rows[0]
        collected_aanwijzing_codes: set[str] = set()

        for field_key in self._config.from_fields:
            field_value: str = getattr(row, field_key)
            fields_aanwijzing_codes: set[str] = _get_aanwijzing_codes(field_value)
            collected_aanwijzing_codes.update(fields_aanwijzing_codes)

        # If we dont have any then we wont need to merge any data back in
        if len(collected_aanwijzing_codes) == 0:
            return rows

        gebieden = self._resolve_codes(collected_aanwijzing_codes)
        setattr(row, self._config.to_field, gebieden)
        rows[0] = row

        return rows

    def _resolve_codes(self, aanwijzing_codes: set[str]):
        # If we do not have a user then we should limit how far in the module you can search for data
        # based on the latest public version of the module
        module_timepoint: datetime = self._resolve_module_timepoint()

        gebied_codes: set[str] = set()
        gebiedengroep_codes: set[str] = set()

        gebiedsaanwijzingen = self._get_latests(module_timepoint, aanwijzing_codes)
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
            gebiedengroepen = self._get_latests(module_timepoint, gebiedengroep_codes)
            for gebiedengroep in gebiedengroepen:
                refs: list[str] = gebiedengroep.Gebieden
                gebied_codes.update(refs)

        if not gebied_codes:
            return []

        gebieden = self._get_latests(module_timepoint, gebied_codes)
        gebieden_parsed = [self._config.to_model.model_validate(gebied) for gebied in gebieden]
        return gebieden_parsed

    def _get_latests(self, module_timepoint: datetime, codes: set[str]) -> Iterator[Base]:
        resolver: AdvancedObjectsResolver = self._object_resolver_factory.create_service(
            self._session,
            self._config.columns,
            self._valid_timepoint,
            module_timepoint,
            filter_codes=codes,
            filter_module_id=self._config.module_id,
        )
        results = resolver.fetch_objects()
        return results

    def _resolve_module_timepoint(self) -> datetime:
        # @todo: implement
        return self._valid_timepoint


class JoinModuleObjectGebiedsaanwijzingenServiceFactory:
    def __init__(self, object_resolver_factory: AdvancedObjectsResolverFactory):
        self._object_resolver_factory: AdvancedObjectsResolverFactory = object_resolver_factory

    def create_service(
        self,
        session: Session,
        config: JoinModuleObjectGebiedsaanwijzingenConfig,
    ) -> JoinModuleObjectGebiedsaanwijzingenService:
        return JoinModuleObjectGebiedsaanwijzingenService(
            session,
            self.object_resolver_factory,
            config,
        )
