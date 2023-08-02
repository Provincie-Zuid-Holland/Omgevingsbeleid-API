from sqlalchemy import String
from sqlalchemy.orm import mapped_column


def extend_with_attributes(table):
    """
    used for declaring dynamic orm properties to a given table on app init
    without placing this logic outside of the extension.
    """
    setattr(table, "Cached_Title", mapped_column("Cached_Title", String(255), nullable=True))
