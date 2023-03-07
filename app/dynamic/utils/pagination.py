from typing import Optional
from dataclasses import dataclass


@dataclass
class Pagination:
    offset: Optional[int] = None
    limit: Optional[int] = None

    def get_offset(self) -> int:
        if self.offset is None:
            return 0
        return self.offset

    def get_limit(self) -> int:
        if self.limit is None:
            return 20
        return self.limit
