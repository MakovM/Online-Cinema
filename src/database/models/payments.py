from datetime import datetime
from sqlalchemy import Integer, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base
from app.models.user import UserModel


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[OrderStatusEnum] = mapped_column(Enum(OrderStatusEnum), default=OrderStatusEnum.PENDING)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=True)

    items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan"
    )
