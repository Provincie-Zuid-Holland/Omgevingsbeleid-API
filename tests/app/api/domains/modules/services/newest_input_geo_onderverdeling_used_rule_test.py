from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.modules.services import NewestInputGeoOnderverdelingUsedRule
from app.api.domains.modules.services.validate_module_service import (
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
        field="Area",
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
                Object_Type="beleidsdoel",  # Not a gebied
                Object_ID="1",
                Code="beleidsdoel-1",
                Title="BD1 title",
            ),
            ModuleObjectsTable(
                Object_Type="gebied",  # No area
                Object_ID="1",
                Code="gebied-1",
                Title="G1 title",
            ),
            ModuleObjectsTable(
                Object_Type="gebied",
                Object_ID="2",
                Code="gebied-2",
                Title="G2 title",
                Area=AreasTable(
                    Source_Geometry_Hash="abc123",  # Onderverdeling existing
                    Source_Title="A1 title",
                ),
            ),
            ModuleObjectsTable(
                Object_Type="gebied",
                Object_ID="3",
                Code="gebied-3",
                Title="G3 title",
                Area=AreasTable(
                    Source_Geometry_Hash="fgh456",  # Onderverdeling no hash match
                    Source_Title="A2 title",
                ),
            ),
            ModuleObjectsTable(
                Object_Type="gebied",
                Object_ID="4",
                Code="gebied-4",
                Title="G4 title",
                Area=AreasTable(
                    Source_Geometry_Hash="ijk789",  # onderverdeling not available
                    Source_Title="A3 title",
                ),
            ),
        ],
    )
    errors: list[ValidateModuleError] = rule.validate(db=db, request=request)
    assert len(errors) == 3
    assert [error.object.code for error in errors] == ["gebied-1", "gebied-3", "gebied-4"]
