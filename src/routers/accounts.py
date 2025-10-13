from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from database.models import UserModel
from database import get_db
from schemas.accounts import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    UserActivationRequestSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    MessageResponseSchema
)

router = APIRouter()


@router.post("/register/", response_model=UserRegistrationResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegistrationRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User with this email already exists.")
    new_user = UserModel(email=user_data.email, password=user_data.password, is_active=False)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserRegistrationResponseSchema.model_validate(new_user)


@router.post("/activate/", response_model=MessageResponseSchema)
async def activate_user(data: UserActivationRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or user.is_active:
        raise HTTPException(status_code=400, detail="Invalid activation or user already active.")
    user.is_active = True
    await db.commit()
    return MessageResponseSchema(message="User activated successfully.")


@router.post("/login/", response_model=UserLoginResponseSchema)
async def login_user(data: UserLoginRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account not activated.")
    access_token = f"access-token-{user.id}"
    refresh_token = f"refresh-token-{user.id}"
    return UserLoginResponseSchema(access_token=access_token, refresh_token=refresh_token)


@router.post("/password-reset/request/", response_model=MessageResponseSchema)
async def request_password_reset(data: PasswordResetRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user:
        user.reset_token = f"reset-{user.id}-{int(datetime.now().timestamp())}"
        await db.commit()
    return MessageResponseSchema(message="If registered, you will receive reset instructions.")


@router.post("/reset-password/complete/", response_model=MessageResponseSchema)
async def reset_password(data: PasswordResetCompleteRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or getattr(user, "reset_token", None) != data.token:
        raise HTTPException(status_code=400, detail="Invalid email or token.")
    user.password = data.password
    user.reset_token = None
    await db.commit()
    return MessageResponseSchema(message="Password reset successfully.")


@router.post("/refresh/", response_model=TokenRefreshResponseSchema)
async def refresh_token(data: TokenRefreshRequestSchema, db: AsyncSession = Depends(get_db)):
    user_id = int(data.refresh_token.split("-")[-1])
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    new_access_token = f"access-token-{user.id}"
    return TokenRefreshResponseSchema(access_token=new_access_token)
