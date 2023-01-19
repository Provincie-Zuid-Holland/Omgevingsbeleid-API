from .compare import Comparator
from .sqlalchemy import Geometry
from .word_filter import get_filtered_search_criteria


def get_limited_list(input_list, limit=None, offset=0):
    """
    Apply limit and offset params to a list as alternative
    to SQLalchemy query pagination.
    """
    if limit is None:
        limit = len(input_list)
    offset = min(offset, len(input_list))
    limit = min(limit, len(input_list) - offset)
    return input_list[offset : offset + limit]
