import pydantic


class ResponseOK(pydantic.BaseModel):
    message: str
