import unittest
from unittest.mock import Mock
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module_service import (
    HoofdlijnenCheckRule,
    HoofdlijnenCheckRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.api.domains.others.repositories.hoofdlijn_repository import HoofdlijnRepository
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable


class HoofdlijnenCheckRuleTest(unittest.TestCase):
    def setUp(self) -> None:
        config: Mock | MainConfig = Mock(MainConfig)
        rule_config: HoofdlijnenCheckRuleConfig = HoofdlijnenCheckRuleConfig(
            field="Hoofdlijnen", allowed_object_types=["ambitie"]
        )
        config.get_as_model.return_value = rule_config

        self._uuid_found: UUID = UUID("1000000-0000-0000-0000-0000000000000")

        repository: HoofdlijnRepository = Mock(HoofdlijnRepository)
        repository.get_existing_uuids.return_value = {self._uuid_found}
        self._rule: HoofdlijnenCheckRule = HoofdlijnenCheckRule(config, repository)
        self._db: Mock | Session = Mock(Session)

    def test_validate(self):
        uuid_missing: UUID = UUID("9999999-9999-9999-9999-9999999999999")
        request: ValidateModuleRequest = ValidateModuleRequest(
            module_id=1,
            module_objects=[
                ModuleObjectsTable(
                    Object_Type="ambitie",  # No hoofdlijnen
                    Object_ID="1",
                    Code="ambitie-1",
                    Title="A1 title",
                ),
                ModuleObjectsTable(
                    Object_Type="ambitie",
                    Object_ID="2",
                    Code="ambitie-2",
                    Title="A2 title",
                    Hoofdlijnen=[str(self._uuid_found)],
                ),
                ModuleObjectsTable(
                    Object_Type="beleidsdoel",  # ignored object type
                    Object_ID="1",
                    Code="beleidsdoel-1",
                    Title="BD1 title",
                ),
                ModuleObjectsTable(
                    Object_Type="ambitie",  # hoofdlijn unknown
                    Object_ID="3",
                    Code="ambitie-3",
                    Title="A3 title",
                    Hoofdlijnen=[str(uuid_missing)],
                ),
            ],
        )

        errors: list[ValidateModuleError] = self._rule.validate(db=self._db, request=request)
        assert len(errors) == 1
        assert [error.object.code for error in errors] == ["ambitie-3"]

    def test_validate_no_hoofdlijnen_attached_to_objects(self):
        request: ValidateModuleRequest = ValidateModuleRequest(
            module_id=1,
            module_objects=[
                ModuleObjectsTable(
                    Object_Type="ambitie",
                    Object_ID="1",
                    Code="ambitie-1",
                    Title="A1 title",
                    Hoofdlijnen=[],
                ),
                ModuleObjectsTable(
                    Object_Type="ambitie",
                    Object_ID="2",
                    Code="ambitie-2",
                    Title="A2 title",
                    Hoofdlijnen=[],
                ),
            ],
        )

        errors: list[ValidateModuleError] = self._rule.validate(db=self._db, request=request)
        assert len(errors) == 0

    def test_validate_no_missing_hoofdlijnen(self):
        request: ValidateModuleRequest = ValidateModuleRequest(
            module_id=1,
            module_objects=[
                ModuleObjectsTable(
                    Object_Type="ambitie",
                    Object_ID="1",
                    Code="ambitie-1",
                    Title="A1 title",
                    Hoofdlijnen=[str(self._uuid_found)],
                ),
                ModuleObjectsTable(
                    Object_Type="ambitie",
                    Object_ID="2",
                    Code="ambitie-2",
                    Title="A2 title",
                    Hoofdlijnen=[str(self._uuid_found)],
                ),
            ],
        )

        errors: list[ValidateModuleError] = self._rule.validate(db=self._db, request=request)
        assert len(errors) == 0
