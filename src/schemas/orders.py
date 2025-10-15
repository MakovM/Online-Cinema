from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from database.models.orders import OrderStatusEnum


class OrderItemResponseSchema(BaseModel):
    id: int
    price_at_order: Decimal


class OrderResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    created_at: datetime
    status: OrderStatusEnum
    items: list[OrderItemResponseSchema]


class OrderItemListScheme(BaseModel):
    model_config = {"from_attributes": True}

    movie_id: int
    price_at_order: Decimal


class OrderListScheme(BaseModel):
    model_config = {"from_attributes": True}

    created_at: datetime
    status: OrderStatusEnum
    items: list[OrderItemListScheme]
    total_amount: Decimal
