import unittest
from unittest.mock import Mock
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module import (
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
            field="hoofdlijnen", allowed_object_types=["ambitie"]
        )
        config.get_as_model.return_value = rule_config

        self._uuid_found: UUID = UUID("10000000-0000-0000-0000-000000000000")

        repository: HoofdlijnRepository = Mock(HoofdlijnRepository)
        repository.get_by_ids.return_value = {self._uuid_found}
        self._rule: HoofdlijnenCheckRule = HoofdlijnenCheckRule(config, repository)
        self._db: Mock | Session = Mock(Session)

    def test_validate(self):
        uuid_missing: UUID = UUID("99999999-9999-9999-9999-999999999999")
        request: ValidateModuleRequest = ValidateModuleRequest(
            module_id=1,
            module_objects=[
                ModuleObjectsTable(
                    object_type="ambitie",  # No hoofdlijnen
                    object_id="1",
                    code="ambitie-1",
                    title="A1 title",
                ),
                ModuleObjectsTable(
                    object_type="ambitie",
                    object_id="2",
                    code="ambitie-2",
                    title="A2 title",
                    hoofdlijnen=[str(self._uuid_found)],
                ),
                ModuleObjectsTable(
                    object_type="beleidsdoel",  # ignored object type
                    object_id="1",
                    code="beleidsdoel-1",
                    title="BD1 title",
                ),
                ModuleObjectsTable(
                    object_type="ambitie",  # hoofdlijn unknown
                    object_id="3",
                    code="ambitie-3",
                    title="A3 title",
                    hoofdlijnen=[str(uuid_missing)],
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
                    object_type="ambitie",
                    object_id="1",
                    code="ambitie-1",
                    title="A1 title",
                    hoofdlijnen=[],
                ),
                ModuleObjectsTable(
                    object_type="ambitie",
                    object_id="2",
                    code="ambitie-2",
                    title="A2 title",
                    hoofdlijnen=[],
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
                    object_type="ambitie",
                    object_id="1",
                    code="ambitie-1",
                    title="A1 title",
                    hoofdlijnen=[str(self._uuid_found)],
                ),
                ModuleObjectsTable(
                    object_type="ambitie",
                    object_id="2",
                    code="ambitie-2",
                    title="A2 title",
                    hoofdlijnen=[str(self._uuid_found)],
                ),
            ],
        )

        errors: list[ValidateModuleError] = self._rule.validate(db=self._db, request=request)
        assert len(errors) == 0
