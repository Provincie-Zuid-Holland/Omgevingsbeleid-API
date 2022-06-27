

def to_ref_field(string: str) -> str:
    """
    Custom alias for relationship objects in json output.
    Used to match the legacy api format: "Ref_*" fields
    """
    to_alias = ["Beleidskeuzes"]

    if string not in to_alias:
        return string

    return "".join(["Ref_", string])
