from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func, DateTime, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base
from database.models.accounts import UserModel
from database.models.movies import Movie


class Cart(Base):
    """Represents a user's shopping cart."""

    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="cart")
    items: Mapped[list["CartItem"]] = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )

    def total_price(self) -> float:
        return sum(item.movie.price for item in self.items)

    def __repr__(self):
        return f"<Cart(id={self.id}, user_id={self.user_id})>"


class CartItem(Base):
    """Represents an item in a user's cart."""

    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    movie: Mapped["Movie"] = relationship("Movie")

    __table_args__ = (UniqueConstraint("cart_id", "movie_id", name="uq_cart_movie"),)

    def __repr__(self):
        return f"<CartItem(id={self.id}, cart_id={self.cart_id}, movie_id={self.movie_id})>"
