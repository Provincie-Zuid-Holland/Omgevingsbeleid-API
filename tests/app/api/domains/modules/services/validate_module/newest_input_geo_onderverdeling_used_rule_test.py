from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module import (
    NewestInputGeoOnderverdelingUsedRule,
    NewestInputGeoOnderverdelingUsedRuleConfig,
    ValidateModuleError,
    ValidateModuleRequest,
)
from app.api.domains.werkingsgebieden.repositories import InputGeoOnderverdelingRepository
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.others import AreasTable
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingenTable


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: NewestInputGeoOnderverdelingUsedRuleConfig = NewestInputGeoOnderverdelingUsedRuleConfig(
        object_type="gebied",
        field="area",
    )
    config.get_as_model.return_value = rule_config
    repository: Mock | InputGeoOnderverdelingRepository = Mock(InputGeoOnderverdelingRepository)
    db: Mock | Session = Mock(Session)

    onderverdeling_area_1: InputGeoOnderverdelingenTable | None = InputGeoOnderverdelingenTable(Geometry_Hash="abc123")
    onderverdeling_area_2: InputGeoOnderverdelingenTable | None = InputGeoOnderverdelingenTable(Geometry_Hash="qwe000")
    onderverdeling_area_3: InputGeoOnderverdelingenTable | None = None

    def fake_get_latest_by_title(_: Mock | Session, title: str):
        return {
            "A1 title": onderverdeling_area_1,
            "A2 title": onderverdeling_area_2,
            "A3 title": onderverdeling_area_3,
        }.get(title)

    repository.get_latest_by_title.side_effect = fake_get_latest_by_title

    rule: NewestInputGeoOnderverdelingUsedRule = NewestInputGeoOnderverdelingUsedRule(config, repository)
    request: ValidateModuleRequest = ValidateModuleRequest(
        module_id=1,
        module_objects=[
            ModuleObjectsTable(
                object_type="beleidsdoel",  # Not a gebied
                object_id="1",
                code="beleidsdoel-1",
                title="BD1 title",
            ),
            ModuleObjectsTable(
                object_type="gebied",  # No area
                object_id="1",
                code="gebied-1",
                title="G1 title",
            ),
            ModuleObjectsTable(
                object_type="gebied",
                object_id="2",
                code="gebied-2",
                title="G2 title",
                area=AreasTable(
                    source_title="A1 title",
                    source_geometry_hash="abc123",  # Onderverdeling existing
                ),
            ),
            ModuleObjectsTable(
                object_type="gebied",
                object_id="3",
                code="gebied-3",
                title="G3 title",
                area=AreasTable(
                    source_title="A2 title",
                    source_geometry_hash="fgh456",  # Onderverdeling no hash match
                ),
            ),
            ModuleObjectsTable(
                object_type="gebied",
                object_id="4",
                code="gebied-4",
                title="G4 title",
                area=AreasTable(
                    source_title="A3 title",
                    source_geometry_hash="ijk789",  # onderverdeling not available
                ),
            ),
        ],
    )
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 3
    assert [error.object.code for error in errors] == ["gebied-1", "gebied-3", "gebied-4"]
