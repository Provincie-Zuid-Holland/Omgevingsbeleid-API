from collections import namedtuple


# Search
SearchFields = namedtuple("SearchFields", ["title", "description"])
RankedSearchObject = namedtuple("RankedSearchObject", ["object", "rank"])


# Endpoints
def to_ref_field(string: str) -> str:
    """
    Custom alias for relationship objects in json output.
    Used to match the legacy api format: "Ref_*" fields
    """
    to_alias = [
        "Beleidsmodules",
    ]

    if string not in to_alias:
        return string

    return "".join(["Ref_", string])


def valid_ref_alias(field: str) -> str:
    aliasses = {
        "Beleidskeuzes": "Ref_Beleidskeuzes",
        "Valid_Beleidskeuzes": "Ref_Beleidskeuzes",
        "Beleidsmodules": "Ref_Beleidsmodules",
        "Valid_Beleidsmodules": "Ref_Beleidsmodules",
    }

    if field in aliasses:
        return aliasses[field]

    return field
