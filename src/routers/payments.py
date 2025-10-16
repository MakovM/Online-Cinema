from datetime import date
from typing import Optional

import stripe
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import get_db, OrderStatusEnum, UserModel, UserGroupEnum
from database.models.payments import PaymentModel, PaymentStatusEnum
from config.settings import Settings
from schemas.payments import PaymentListResponseScheme
from security.dependencies import get_current_user

router = APIRouter()
settings = Settings()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[PaymentListResponseScheme],
)
async def list_payments(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    user_id: Optional[int] = None,
    date_filter: Optional[date] = None,
    status_filter: Optional[OrderStatusEnum] = None,
):
    try:
        query = (
            select(PaymentModel)
            .options(
                selectinload(PaymentModel.items),
            )
            .order_by(PaymentModel.created_at.desc())
        )

        if current_user.has_group(UserGroupEnum.ADMIN) or current_user.has_group(
            UserGroupEnum.MODERATOR
        ):
            if user_id:
                query = query.where(PaymentModel.user_id == user_id)
            if date_filter:
                query = query.where(func.date(PaymentModel.created_at) >= date_filter)
            if status_filter:
                query = query.where(PaymentModel.status == status_filter)
        else:
            query = query.where(PaymentModel.user_id == current_user.id)

        result = await db.execute(query)
        payments = result.scalars().unique().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return payments


@router.post("/webhook/")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Stripe Webhook endpoint"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    if event["type"] in ["checkout.session.completed", "checkout.session.expired"]:
        session = event["data"]["object"]
        session_id = session.get("id")
        stmt = (
            select(PaymentModel)
            .options(selectinload(PaymentModel.order))
            .where(PaymentModel.session_id == session_id)
        )
        result = await db.execute(stmt)
        payment = result.scalars().first()

        if payment and payment.status == PaymentStatusEnum.PENDING:
            if event["type"] == "checkout.session.completed":
                payment.status = PaymentStatusEnum.SUCCESSFUL
                payment.order.status = OrderStatusEnum.PAID
            else:
                payment.status = PaymentStatusEnum.EXPIRED
                payment.order.status = OrderStatusEnum.EXPIRED
            await db.commit()


@router.get("/success/", status_code=status.HTTP_200_OK)
async def payment_success(session_id: str):
    """Stripe success URL endpoint"""

    return {"detail": "Payment successful!"}


@router.get("/cancel/", status_code=status.HTTP_200_OK)
async def payment_cancel():
    """Stripe cancel URL endpoint"""

    return {"detail": "Payment canceled. You can try again."}
