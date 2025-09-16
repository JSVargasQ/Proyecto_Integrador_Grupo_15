from typing import List

from pydantic import BaseModel


class Location(BaseModel):
    latitude: float
    longitude: float


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    warehouse_id: str
    warehouse_location: str


class ClientInfo(BaseModel):
    id: str
    name: str
    location: str


class RequestBody(BaseModel):
    order_id: str
    order_items: List[OrderItem]
    client: ClientInfo


class RouteOptimizationResponse(BaseModel):
    performed_shipment_count: int
    total_duration: int
    travel_distance_meters: int
    total_cost: float


class GenericResponse(BaseModel):
    msg: str
