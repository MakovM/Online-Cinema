import enum
from datetime import datetime
from typing import List

from sqlalchemy import (
    ForeignKey,
    String,
    Boolean,
    DateTime,
    Enum,
    Integer,
    func,
    Text,
    Date,
    UniqueConstraint,
    DECIMAL,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from database.models.orders import OrderModel, OrderItemModel


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="payments")

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="payments")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum), nullable=False, default=PaymentStatusEnum.PENDING
    )

    amount: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), nullable=True)

    session_id: Mapped[str] = mapped_column(String, nullable=True)

    session_url: Mapped[str] = mapped_column(String, nullable=True)

    items: Mapped[List["PaymentItemModel"]] = relationship(
        "PaymentItemModel", back_populates="payment", cascade="all, delete-orphan"
    )


class PaymentItemModel(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )
    payment: Mapped["PaymentModel"] = relationship("PaymentModel", back_populates="items")

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False
    )
    order_item: Mapped["OrderItemModel"] = relationship("OrderItemModel")

    price_at_payment: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), nullable=False)
