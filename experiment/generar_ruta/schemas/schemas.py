from pydantic import BaseModel


class Location(BaseModel):
    latitude: float
    longitude: float


class RequestBody(BaseModel):
    order_id: str
    start_location: str
    end_location: str


class GenericResponse(BaseModel):
    msg: str
