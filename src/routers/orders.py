from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db

from database.models.accounts import UserModel
from schemas import OrderListScheme
from security.dependencies import get_current_user

from database.models.carts import Cart, CartItem
from database.models.orders import OrderItemModel, OrderModel, OrderStatusEnum
from database.models.accounts import UserGroupEnum

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
        db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)
):
    """Endpoint for creating an order"""
    cart_query = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.movie))
        .join(Cart)
        .where(Cart.user_id == current_user.id)
    )
    cart_items = cart_query.scalars().all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    available_movies = []
    for item in cart_items:
        result = await db.execute(
            select(OrderItemModel)
            .join(OrderModel)
            .where(
                OrderItemModel.movie_id == item.movie_id,
                or_(
                    OrderModel.status == OrderStatusEnum.PENDING,
                    OrderModel.status == OrderStatusEnum.PAID
                )
            )
        )
        if result.scalars().first():
            continue

        available_movies.append(item)

    if not available_movies:
        raise HTTPException(status_code=400, detail="No available movies to create order")

    order = OrderModel(
        user_id=current_user.id,
        status=OrderStatusEnum.PENDING,
        total_amount=Decimal(0.00)
    )
    db.add(order)
    await db.flush()

    total = Decimal(0.00)
    for item in available_movies:
        order_item = OrderItemModel(
            order_id=order.id,
            movie_id=item.movie_id,
            price_at_order=Decimal(item.movie.price)
        )
        db.add(order_item)
        total += Decimal(item.movie.price)
        await db.delete(item)

    order.total_amount = total

    await db.commit()
    await db.refresh(order)

    return order


@router.post("/cancel/{order_id}/", status_code=status.HTTP_200_OK)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Endpoint for cancelling an order"""
    order = await db.get(OrderModel, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == OrderStatusEnum.PAID:
        raise HTTPException(
            status_code=400,
            detail="Paid orders cannot be canceled; request a refund instead"
        )

    order.status = OrderStatusEnum.CANCELED

    await db.commit()
    await db.refresh(order)

    return {"detail": f"Order has been canceled successfully."}


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderListScheme],
)
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[OrderStatusEnum] = None,
):
    query = (
        select(OrderModel)
        .options(selectinload(OrderModel.items).selectinload(OrderItemModel.movie))
        .order_by(OrderModel.created_at.desc())
    )

    if not current_user.has_group(UserGroupEnum.ADMIN) and not current_user.has_group(UserGroupEnum.MODERATOR):
        query = query.where(OrderModel.user_id == current_user.id)

    if user_id:
        query = query.where(OrderModel.user_id == user_id)

    if start_date:
        query = query.where(OrderModel.created_at >= start_date)

    if end_date:
        query = query.where(OrderModel.created_at <= end_date)

    if status_filter:
        query = query.where(OrderModel.status == status_filter)

    result = await db.execute(query)
    orders = result.scalars().unique().all()

    return orders
