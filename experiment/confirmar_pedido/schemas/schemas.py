from pydantic import BaseModel


class RequestBody(BaseModel):
    order_id: str


class GenericResponse(BaseModel):
    msg: str