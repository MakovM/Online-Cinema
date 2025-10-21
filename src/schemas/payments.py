from datetime import datetime

from pydantic import BaseModel
from decimal import Decimal
from database import PaymentStatusEnum


class PaymentOrderResponseScheme(BaseModel):
    model_config = {"from_attributes": True}

    session_id: str
    session_url: str


class PaymentOrderListScheme(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    created_at: datetime
    status: PaymentStatusEnum
    amount: Decimal


class PaymentItemListResponseScheme(BaseModel):
    model_config = {"from_attributes": True}

    order_item_id: int
    price_at_payment: Decimal


class PaymentListResponseScheme(PaymentOrderListScheme):
    items: list[PaymentItemListResponseScheme]
