from typing import List

from pydantic import BaseModel


class Location(BaseModel):
    latitude: float
    longitude: float


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    warehouse_location: str


class RequestBody(BaseModel):
    order_id: str
    order_items: List[OrderItem]
    client: str
    client_location: str


class GenericResponse(BaseModel):
    msg: str
