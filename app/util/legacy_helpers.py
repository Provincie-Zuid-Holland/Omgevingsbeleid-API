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
        "Belangen",
        "Beleidsdoelen",
        "Beleidskeuzes",
        "Beleidsmodules",
        "Beleidsprestaties",
        "Beleidsrelaties",
        "Beleidsregels",
        "Verordeningen",
        "Maatregelen",
    ]

    if string not in to_alias:
        return string

    return "".join(["Ref_", string])
