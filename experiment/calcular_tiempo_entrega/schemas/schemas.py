from datetime import datetime
from typing import List
from pydantic import BaseModel


class ClientInfo(BaseModel):
    id: str
    name: str
    location: str


class ProductOrder(BaseModel):
    product_id: str
    quantity: int
    warehouse_id: str
    warehouse_location: str


class Order(BaseModel):
    order_id: str
    created_at: datetime
    order_items: List[ProductOrder]
    client: ClientInfo


class RouteInfo(BaseModel):
    performed_shipment_count: int
    total_duration: int
    travel_distance_meters: int
    total_cost: float


class GenericResponse(BaseModel):
    msg: str
