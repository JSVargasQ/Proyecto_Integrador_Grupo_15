from typing import List

from pydantic import BaseModel


class ClientInfo(BaseModel):
    id: str
    name: str
    location: str


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    warehouse_id: str
    warehouse_location: str


class RequestBody(BaseModel):
    order_id: str
    order_items: List[OrderItem]
    client: ClientInfo
