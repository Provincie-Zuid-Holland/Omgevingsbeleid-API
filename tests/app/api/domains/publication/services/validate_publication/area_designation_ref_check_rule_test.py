from unittest.mock import Mock

from dso import Gebiedsaanwijzingen, GebiedsaanwijzingenFactory
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingWaarde
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication import (
    AreaDesignationRefCheckRule,
    ValidatePublicationError,
    ValidatePublicationRequest,
)
from app.api.domains.publications.types.api_input_data import PublicationGebiedsaanwijzing
from app.api.domains.publications.types.enums import DocumentType
from tests.app.api.domains.publication.services.validate_publication.type_factories import (
    make_api_act_input_data,
    make_publication_data,
    make_publication_gebiedsaanwijzing,
)
from tests.dso.factories.gebiedsaanwijzing import make_gebiedsaanwijzing as make_dso_gebiedsaanwijzing


def test_validate():
    gebiedsaanwijzing_1 = make_dso_gebiedsaanwijzing(deprecated=False)
    gebiedsaanwijzing_2 = make_dso_gebiedsaanwijzing(deprecated=True)

    def fake_get_by_type_label(ref: str) -> Mock | Gebiedsaanwijzing | None:
        return {
            "ref_1": gebiedsaanwijzing_1,
            "ref_2": None,
            "ref_3": gebiedsaanwijzing_2,
        }.get(ref)

    gebiedsaanwijzingen: Mock | Gebiedsaanwijzingen = Mock(Gebiedsaanwijzingen)
    gebiedsaanwijzingen.get_by_type_label.side_effect = fake_get_by_type_label

    waarde_1: Mock | GebiedsaanwijzingWaarde = Mock(GebiedsaanwijzingWaarde)
    waarde_1.deprecated = False
    waarde_2: Mock | GebiedsaanwijzingWaarde = Mock(GebiedsaanwijzingWaarde)
    waarde_2.deprecated = True

    def fake_get_value_by_label(ref_group: str) -> Mock | GebiedsaanwijzingWaarde | None:
        return {
            "ref_group_1": waarde_1,
            "ref_group_2": None,
            "ref_group_3": waarde_2,
        }.get(ref_group)

    gebiedsaanwijzing_1.get_value_by_label.side_effect = fake_get_value_by_label

    factory: GebiedsaanwijzingenFactory = Mock(GebiedsaanwijzingenFactory)
    factory.get_for_document.return_value = gebiedsaanwijzingen

    gebiedsaanwijzingen_request: dict[str, PublicationGebiedsaanwijzing] = {
        "gebiedsaanwijzing-1": make_publication_gebiedsaanwijzing(
            code="gebiedsaanwijzing-1", aanwijzing_type="ref_1", aanwijzing_group="ref_group_1", title="GA1 title"
        ),
        "gebiedsaanwijzing-2": make_publication_gebiedsaanwijzing(
            code="gebiedsaanwijzing-2",
            aanwijzing_type="ref_2",
            title="GA2 title",  # ref type None
        ),
        "gebiedsaanwijzing-3": make_publication_gebiedsaanwijzing(
            code="gebiedsaanwijzing-3",
            aanwijzing_type="ref_3",
            title="GA3 title",  # ref type deprecated
        ),
        "gebiedsaanwijzing-4": make_publication_gebiedsaanwijzing(
            code="gebiedsaanwijzing-4",
            aanwijzing_type="ref_1",
            aanwijzing_group="ref_group_2",
            title="GA4 title",  # ref group None
        ),
        "gebiedsaanwijzing-5": make_publication_gebiedsaanwijzing(
            code="gebiedsaanwijzing-5",
            aanwijzing_type="ref_1",
            aanwijzing_group="ref_group_3",
            title="GA5 title",  # ref group deprecated
        ),
    }
    rule: AreaDesignationRefCheckRule = AreaDesignationRefCheckRule(factory)
    request: ValidatePublicationRequest = ValidatePublicationRequest(
        input_data=make_api_act_input_data(
            Publication_Data=make_publication_data(gebiedsaanwijzingen=gebiedsaanwijzingen_request)
        ),
        document_type=DocumentType.VISION,
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidatePublicationError] = rule.validate(db=db, request=request)
    assert len(errors) == 4
    assert [error.object.code for error in errors] == [
        "gebiedsaanwijzing-2",
        "gebiedsaanwijzing-3",
        "gebiedsaanwijzing-4",
        "gebiedsaanwijzing-5",
    ]
