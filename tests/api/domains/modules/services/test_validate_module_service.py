import uuid
from unittest.mock import ANY, call

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.domains.modules.services import RequiredHierarchyCodeRule
from app.api.domains.modules.services.validate_module_service import ValidateModuleService, \
    ValidateModuleRequest, RequiredObjectFieldsRule, NewestSourceWerkingsgebiedUsedRule
from app.api.domains.werkingsgebieden.repositories import WerkingsgebiedenRepository
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.others import AreasTable
from app.core.tables.werkingsgebieden import SourceWerkingsgebiedenTable


class Ambitie(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    Title: str


class TestValidateModuleService:
    def test_validate(self, mocker):
        object_map = {
            "ambitie": Ambitie,
        }
        required_object_fields_rule = RequiredObjectFieldsRule(object_map)

        publication_object_repository_result = [
            {
                "Code": "ambitie-1",
                "Hierarchy_Code": None,
            },
            {
                "Code": "ambitie-2",
                "Hierarchy_Code": "ambitie-1",
            },
            {
                "Code": "ambitie-3",
                "Hierarchy_Code": "ambitie-unknown",
            },  # Hierarchy_Code doesn't exist, errors +1
        ]
        publication_object_repository = mocker.patch(
            "app.api.domains.publications.repository.PublicationObjectRepository",
            return_value=publication_object_repository_result)
        publication_object_repository.fetch_objects.return_value = publication_object_repository_result

        required_hierarchy_code_rule = RequiredHierarchyCodeRule(publication_object_repository)

        werkingsgebieden_repository: WerkingsgebiedenRepository = mocker.patch(
            "app.api.domains.werkingsgebieden.repositories.WerkingsgebiedenRepository")
        newest_source_werkingsgebied_used_rule = NewestSourceWerkingsgebiedUsedRule(werkingsgebieden_repository)
        shape: bytes = b"some-shape"
        area_latest: SourceWerkingsgebiedenTable = SourceWerkingsgebiedenTable(SHAPE=shape)
        werkingsgebieden_repository.get_latest_by_title.return_value = area_latest

        service: ValidateModuleService = ValidateModuleService([
            required_object_fields_rule,
            required_hierarchy_code_rule,
            newest_source_werkingsgebied_used_rule,
        ])

        module_object_ambitie_1 = ModuleObjectsTable(Title="ambitie 1", Object_Type="ambitie", Code="ambitie-1")
        module_object_ambitie_2 = ModuleObjectsTable(Object_Type="ambitie", Code="ambitie-2")  # misses Title, errors +1

        area_uuid = uuid.UUID("11111111-0000-0000-0000-000000000001")
        area_up_to_date: AreasTable = AreasTable(UUID=area_uuid, Source_Title="some-up-to-date-area", Shape=shape)
        module_object_werkingsgebied_1 = ModuleObjectsTable(Object_Type="werkingsgebied", Code="werkingsgebied-1", Area=area_up_to_date)

        shape_outdated: bytes = b"some-outdated-shape"
        area_out_of_date: AreasTable = AreasTable(UUID=area_uuid, Source_Title="some-out-of-date-area", Shape=shape_outdated)
        module_object_werkingsgebied_2 = ModuleObjectsTable(Object_Type="werkingsgebied", Code="werkingsgebied-2", Area=area_out_of_date)  # area shape is not current, errors +1

        area_no_shape: AreasTable = AreasTable(UUID=area_uuid, Source_Title="some-area-without-shape", Shape=None)
        module_object_werkingsgebied_3 = ModuleObjectsTable(Object_Type="werkingsgebied", Code="werkingsgebied-3", Area=area_no_shape)  # area without shape, errors +1
        request = ValidateModuleRequest(
            module_id=1,
            module_objects=[
                module_object_ambitie_1,
                module_object_ambitie_2,
                module_object_werkingsgebied_1,
                module_object_werkingsgebied_2,
                module_object_werkingsgebied_3,
            ]
        )

        db: Session = mocker.patch("sqlalchemy.orm.Session")

        result = service.validate(db, request)
        assert len(result.errors) == 4
        publication_object_repository.fetch_objects.assert_called_once_with(db, 1, ANY)

        werkingsgebieden_repository.get_latest_by_title.assert_has_calls([
            call(db, "some-up-to-date-area"),
            call(db, "some-out-of-date-area"),
        ])
