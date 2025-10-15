import enum
from datetime import datetime
from typing import List, Optional

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
from database.models.accounts import UserModel
from database.models.movies import Movie


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"
    EXPIRED = "expired"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    status: Mapped[OrderStatusEnum] = mapped_column(
        Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.PENDING
    )

    total_amount: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), nullable=True)

    items: Mapped[List["OrderItemModel"]] = relationship(
        "OrderItemModel", back_populates="order", cascade="all, delete-orphan"
    )

    payments: Mapped[List["PaymentModel"]] = relationship(
        "PaymentModel", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[OrderModel] = relationship("OrderModel", back_populates="items")

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    movie: Mapped[Movie] = relationship("Movie")

    price_at_order: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), nullable=False)
