from fastapi import Request, status
from fastapi.responses import JSONResponse

# Exceptions
class DatabaseError(Exception):
    pass


class QueryParamValidation(Exception):
    pass


class FilterNotAllowed(Exception):
    def __init__(self, filter: str):
        self.filter = filter


# Handlers
def filter_valdiation_handler(request: Request, exc: FilterNotAllowed):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": f"Following filter is invalid or not allowed for this model: {exc.filter}"
        },
    )
