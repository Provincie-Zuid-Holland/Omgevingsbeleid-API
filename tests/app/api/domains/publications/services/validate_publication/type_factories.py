from datetime import date

from app.api.domains.publications.types.api_input_data import (
    ActFrbr,
    ActMutation,
    ApiActInputData,
    BillFrbr,
    PublicationData,
    PublicationGebiedsaanwijzing,
    Purpose,
)
from app.api.domains.publications.types.enums import MutationStrategy, PackageType, PurposeType
from app.core.tables.publications import PublicationVersionTable


def make_bill_frbr(**overrides) -> BillFrbr:
    defaults = {
        "work_province_id": "pv28",
        "work_country": "nl",
        "work_date": "2024",
        "work_other": "omgevingsvisie-1",
        "expression_language": "nld",
        "expression_date": "2024-01-01",
        "expression_version": 1,
    }
    defaults.update(overrides)
    return BillFrbr(**defaults)


def make_act_frbr(**overrides) -> ActFrbr:
    defaults = {
        "act_id": 1,
        "work_province_id": "pv28",
        "work_country": "nl",
        "work_date": "2024",
        "work_other": "omgevingsvisie-1",
        "expression_language": "nld",
        "expression_date": "2024-01-01",
        "expression_version": 1,
    }
    defaults.update(overrides)
    return ActFrbr(**defaults)


def make_purpose(**overrides) -> Purpose:
    defaults = {
        "purpose_type": PurposeType.CONSOLIDATION,
        "effective_date": date(2024, 1, 1),
        "work_province_id": "pv28",
        "work_date": "2024",
        "work_other": "omgevingsvisie-1",
    }
    defaults.update(overrides)
    return Purpose(**defaults)


def make_act_mutation(**overrides) -> ActMutation:
    defaults = {
        "consolidated_act_frbr": make_act_frbr(),
        "consolidated_act_text": "",
        "known_wid_map": {},
        "known_wids": [],
        "removed_gios": [],
    }
    defaults.update(overrides)
    return ActMutation(**defaults)


def make_publication_data(**overrides) -> PublicationData:
    defaults = {
        "all_object_codes": set(),
        "all_objects": [],
        "used_object_codes": set(),
        "used_objects": [],
        "documents": [],
        "assets": [],
        "gios": {},
        "gebiedengroepen": {},
        "gebiedsaanwijzingen": {},
        "bill_attachments": [],
        "area_of_jurisdiction": {},
        "parsed_template": "",
    }
    defaults.update(overrides)
    return PublicationData(**defaults)


def make_api_act_input_data(**overrides) -> ApiActInputData:
    defaults = {
        "bill_frbr": make_bill_frbr(),
        "act_frbr": make_act_frbr(),
        "consolidation_purpose": make_purpose(),
        "publication_data": make_publication_data(),
        "package_type": PackageType.VALIDATION,
        "publication_version": PublicationVersionTable(),
        "act_mutation": None,
        "ow_state": None,
        "mutation_strategy": MutationStrategy.RENVOOI,
    }
    defaults.update(overrides)
    return ApiActInputData(**defaults)


def make_publication_gebiedsaanwijzing(**overrides) -> PublicationGebiedsaanwijzing:
    defaults = {
        "id": "",
        "code": "",
        "title": "",
        "aanwijzing_type": "",
        "aanwijzing_group": "",
        "gio_key": "",
        "source_target_codes": set(),
        "resolved_gebied_codes": set(),
    }
    defaults.update(overrides)
    return PublicationGebiedsaanwijzing(**defaults)
