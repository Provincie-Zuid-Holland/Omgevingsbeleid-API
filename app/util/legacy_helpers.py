from app.core.exceptions import QueryParamValidation


def parse_filter_str(filter_str: str):
    """
    Converts the legacy query param string format to dict
    Legacy format: 'foo:value,bar:value'

    Returns:
        Dict: A dictionary that contains the filters
    """
    filters = dict()

    if len(filter_str) == 0:
        return filters

    for filter_item in filter_str.split(","):
        tp = tuple(filter_item.split(":"))
        filters[tp[0]] = tp[1]
    
    return filters



def to_ref_field(string: str) -> str:
    """
    Custom alias for relationship objects in json output.
    Used to match the legacy api format: "Ref_*" fields
    """
    to_alias = ["Beleidskeuzes"]

    if string not in to_alias: 
        return string
    
    return "".join(["Ref_", string])