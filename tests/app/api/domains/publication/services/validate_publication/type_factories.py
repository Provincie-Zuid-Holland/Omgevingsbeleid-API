from datetime import date

from app.api.domains.publications.types.api_input_data import (
    ActFrbr,
    ActMutation,
    ApiActInputData,
    BillFrbr,
    PublicationData,
    Purpose,
)
from app.api.domains.publications.types.enums import MutationStrategy, PackageType, PurposeType
from app.core.tables.publications import PublicationVersionTable


def make_bill_frbr(**overrides) -> BillFrbr:
    defaults = {
        "Work_Province_ID": "pv28",
        "Work_Country": "nl",
        "Work_Date": "2024",
        "Work_Other": "omgevingsvisie-1",
        "Expression_Language": "nld",
        "Expression_Date": "2024-01-01",
        "Expression_Version": 1,
    }
    defaults.update(overrides)
    return BillFrbr(**defaults)


def make_act_frbr(**overrides) -> ActFrbr:
    defaults = {
        "Act_ID": 1,
        "Work_Province_ID": "pv28",
        "Work_Country": "nl",
        "Work_Date": "2024",
        "Work_Other": "omgevingsvisie-1",
        "Expression_Language": "nld",
        "Expression_Date": "2024-01-01",
        "Expression_Version": 1,
    }
    defaults.update(overrides)
    return ActFrbr(**defaults)


def make_purpose(**overrides) -> Purpose:
    defaults = {
        "Purpose_Type": PurposeType.CONSOLIDATION,
        "Effective_Date": date(2024, 1, 1),
        "Work_Province_ID": "pv28",
        "Work_Date": "2024",
        "Work_Other": "omgevingsvisie-1",
    }
    defaults.update(overrides)
    return Purpose(**defaults)


def make_act_mutation(**overrides) -> ActMutation:
    defaults = {
        "Consolidated_Act_Frbr": make_act_frbr(),
        "Consolidated_Act_Text": "",
        "Known_Wid_Map": {},
        "Known_Wids": [],
        "Removed_Gios": [],
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
        "Bill_Frbr": make_bill_frbr(),
        "Act_Frbr": make_act_frbr(),
        "Consolidation_Purpose": make_purpose(),
        "Publication_Data": make_publication_data(),
        "Package_Type": PackageType.VALIDATION,
        "Publication_Version": PublicationVersionTable(),
        "Act_Mutation": None,
        "Ow_State": None,
        "Mutation_Strategy": MutationStrategy.RENVOOI,
    }
    defaults.update(overrides)
    return ApiActInputData(**defaults)
