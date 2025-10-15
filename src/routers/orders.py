from datetime import date
from decimal import Decimal
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db

from database.models.accounts import UserModel
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatusEnum
from schemas import OrderListScheme
from schemas.orders import OrderCreationResponseScheme, OrderListResponseScheme
from security.dependencies import get_current_user

from database.models.carts import Cart, CartItem
from database.models.orders import OrderItemModel, OrderModel, OrderStatusEnum
from database.models.accounts import UserGroupEnum
from utils.payments import StripePayment

router = APIRouter()


@router.post(
    "/",
    response_model=OrderCreationResponseScheme,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Endpoint for order creation"""
    try:
        cart_items = (
            await db.execute(
                select(CartItem)
                .options(selectinload(CartItem.movie))
                .join(Cart)
                .where(Cart.user_id == current_user.id)
            )
        ).scalars().all()

        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        movie_ids = [item.movie_id for item in cart_items]
        movies_in_orders = set(
            (await db.execute(
                select(OrderItemModel.movie_id)
                .join(OrderModel)
                .where(
                    OrderItemModel.movie_id.in_(movie_ids),
                    OrderModel.user_id == current_user.id,
                    OrderModel.status.in_([OrderStatusEnum.PENDING, OrderStatusEnum.PAID])
                )
            )).scalars().all()
        )

        available_movies = [item for item in cart_items if item.movie_id not in movies_in_orders]

        if not available_movies:
            raise HTTPException(status_code=400, detail="No available movies to create order")

        order = OrderModel(user_id=current_user.id, status=OrderStatusEnum.PENDING)
        db.add(order)
        await db.flush()

        total = Decimal(0.0)
        order_items = []
        for item in available_movies:
            order_item = OrderItemModel(
                order_id=order.id,
                movie_id=item.movie_id,
                price_at_order=Decimal(item.movie.price)
            )
            db.add(order_item)
            await db.flush()
            order_items.append(order_item)
            total += Decimal(item.movie.price)
            await db.delete(item)

        order.total_amount = total

        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": item.movie.name},
                    "unit_amount": int(item.movie.price * 100),
                },
                "quantity": 1,
            }
            for item in available_movies
        ]
        session = StripePayment(line_items).create_session(order, current_user)

        payment = PaymentModel(
            user_id=current_user.id,
            order_id=order.id,
            amount=total,
            session_id=session.id,
            session_url=session.url
        )
        db.add(payment)
        await db.flush()

        for order_item in order_items:
            db.add(PaymentItemModel(
                payment_id=payment.id,
                order_item_id=order_item.id,
                price_at_payment=order_item.price_at_order
            ))

        await db.commit()
        await db.refresh(order)

        order = await db.execute(
            select(OrderModel)
            .options(
                selectinload(OrderModel.items).selectinload(OrderItemModel.movie),
                selectinload(OrderModel.payments)
            )
            .where(OrderModel.id == order.id)
        )
        order = order.scalars().first()

    except (SQLAlchemyError, stripe.error.StripeError) as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error occurred.")

    return order



@router.post("/cancel/{order_id}/", status_code=status.HTTP_200_OK)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Endpoint for cancelling an order"""
    order = await db.get(OrderModel, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == OrderStatusEnum.PAID:
        raise HTTPException(
            status_code=400, detail="Paid orders cannot be canceled; request a refund instead"
        )
    if order.status == OrderStatusEnum.CANCELED:
        raise HTTPException(status_code=400, detail="Order already canceled")
    try:
        order.status = OrderStatusEnum.CANCELED

        await db.execute(
            update(PaymentModel)
            .where(PaymentModel.order_id == order_id, PaymentModel.status == PaymentStatusEnum.PENDING)
            .values(status=PaymentStatusEnum.CANCELED)
        )


        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"detail": "Order has been canceled successfully."}


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderListResponseScheme],
)
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    user_id: Optional[int] = None,
    date_filter: Optional[date] = None,
    status_filter: Optional[OrderStatusEnum] = None,
):
    try:
        query = (
            select(OrderModel)
            .options(
                selectinload(OrderModel.items).selectinload(OrderItemModel.movie),
                selectinload(OrderModel.payments),
            )
            .order_by(OrderModel.created_at.desc())
        )

        if current_user.has_group(UserGroupEnum.ADMIN) or current_user.has_group(
            UserGroupEnum.MODERATOR
        ):
            if user_id:
                query = query.where(OrderModel.user_id == user_id)
            if date_filter:
                query = query.where(func.date(OrderModel.created_at) >= date_filter)
            if status_filter:
                query = query.where(OrderModel.status == status_filter)
        else:
            query = query.where(OrderModel.user_id == current_user.id)

        result = await db.execute(query)
        orders = result.scalars().unique().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return orders
