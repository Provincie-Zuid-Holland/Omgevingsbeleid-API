from dso import Gebiedsaanwijzingen, GebiedsaanwijzingenFactory
from dso.models import DocumentType
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingWaarde
from sqlalchemy.orm import Session

from app.api.domains.publications.services.act_package.dso_act_input_data_builder import DOCUMENT_TYPE_MAP
from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
    ValidatePublicationSeverity,
)


class AreaDesignationRefCheckRule(ValidatePublicationRule):
    def __init__(self, dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory):
        self._dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory = dso_gebiedsaanwijzingen_factory

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        dso_document_type: DocumentType = DOCUMENT_TYPE_MAP[request.document_type]
        gebiedsaanwijzingen: Gebiedsaanwijzingen | None = self._dso_gebiedsaanwijzingen_factory.get_for_document(
            dso_document_type
        )

        for gebiedsaanwijzing in request.input_data.Publication_Data.gebiedsaanwijzingen.values():
            object_type, object_id = gebiedsaanwijzing.code.split("-", 1)
            ref_type: Gebiedsaanwijzing | None = gebiedsaanwijzingen.get_by_type_label(
                gebiedsaanwijzing.aanwijzing_type
            )

            if ref_type is None:
                errors.append(
                    ValidatePublicationError(
                        rule="area_designation_check_ref_rule",
                        object=ValidatePublicationObject(
                            code=gebiedsaanwijzing.code,
                            object_id=int(object_id),
                            object_type=object_type,
                            title=gebiedsaanwijzing.title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingType '{gebiedsaanwijzing.aanwijzing_type}' for gebiedsaanwijzing not found"
                        ],
                    )
                )
                continue
            if ref_type.aanwijzing_type.deprecated:
                errors.append(
                    ValidatePublicationError(
                        rule="area_designation_check_ref_rule",
                        object=ValidatePublicationObject(
                            code=gebiedsaanwijzing.code,
                            object_id=int(object_id),
                            object_type=object_type,
                            title=gebiedsaanwijzing.title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingType '{gebiedsaanwijzing.aanwijzing_type}' for gebiedsaanwijzing is deprecated"
                        ],
                    )
                )
                continue

            ref_group: GebiedsaanwijzingWaarde | None = ref_type.get_value_by_label(gebiedsaanwijzing.aanwijzing_group)
            if ref_group is None:
                errors.append(
                    ValidatePublicationError(
                        rule="area_designation_check_ref_rule",
                        object=ValidatePublicationObject(
                            code=gebiedsaanwijzing.code,
                            object_id=int(object_id),
                            object_type=object_type,
                            title=gebiedsaanwijzing.title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingGroep '{gebiedsaanwijzing.aanwijzing_group}' for GebiedsaanwijzingType '{gebiedsaanwijzing.aanwijzing_type}' not found"
                        ],
                    )
                )
                continue
            if ref_group.deprecated:
                errors.append(
                    ValidatePublicationError(
                        rule="area_designation_check_ref_rule",
                        object=ValidatePublicationObject(
                            code=gebiedsaanwijzing.code,
                            object_id=int(object_id),
                            object_type=object_type,
                            title=gebiedsaanwijzing.title,
                        ),
                        severity=ValidatePublicationSeverity.warning,
                        messages=[
                            f"GebiedsaanwijzingGroep '{gebiedsaanwijzing.aanwijzing_group}' for GebiedsaanwijzingType '{gebiedsaanwijzing.aanwijzing_type}' is deprecated"
                        ],
                    )
                )
        return errors
