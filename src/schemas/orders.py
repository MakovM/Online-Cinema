from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from database.models import OrderStatusEnum


class BaseOrderItemScheme(BaseModel):
    movie_id: int
    price_at_order: Decimal


class OrderItemListScheme(BaseOrderItemScheme):
    pass

    model_config = {"from_attributes": True}

class BaseOrderScheme(BaseModel):
    user_id: int
    created_at: datetime
    status: OrderStatusEnum
    items: list[OrderItemListScheme]


class OrderListScheme(BaseOrderScheme):
    id: int

    model_config = {"from_attributes": True}
