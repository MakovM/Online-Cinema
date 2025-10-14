from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from database.models import UserModel, UserGroupModel, UserGroupEnum
from database.session_postgresql import get_postgresql_db
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
    MessageResponseSchema,
)
from security.token_manager import JWTAuthManager
from config import get_settings


settings = get_settings()
jwt_manager = JWTAuthManager(
    secret_key_access=settings.SECRET_KEY_ACCESS,
    secret_key_refresh=settings.SECRET_KEY_REFRESH,
    algorithm=settings.JWT_SIGNING_ALGORITHM,
)

router = APIRouter()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserRegistrationRequestSchema, db: AsyncSession = Depends(get_postgresql_db)
):
    stmt = select(UserModel).where(UserModel.email == user_data.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="User with this email already exists.")

    stmt_group = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    result_group = await db.execute(stmt_group)
    user_group = result_group.scalars().first()
    if not user_group:
        raise HTTPException(status_code=500, detail="Default user group missing.")

    new_user = UserModel(email=user_data.email, group_id=user_group.id)
    new_user.password = user_data.password

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
async def login_user(data: UserLoginRequestSchema, db: AsyncSession = Depends(get_postgresql_db)):
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.verify_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account not activated.")

    access_token = jwt_manager.create_access_token({"sub": str(user.id)})
    refresh_token = jwt_manager.create_refresh_token({"sub": str(user.id)})

    return UserLoginResponseSchema(access_token=access_token, refresh_token=refresh_token)


@router.post("/password-reset/request/", response_model=MessageResponseSchema)
async def request_password_reset(
    data: PasswordResetRequestSchema, db: AsyncSession = Depends(get_db)
):
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user:
        user.reset_token = f"reset-{user.id}-{int(datetime.now().timestamp())}"
        await db.commit()
    return MessageResponseSchema(message="If registered, you will receive reset instructions.")


@router.post("/reset-password/complete/", response_model=MessageResponseSchema)
async def reset_password(
    data: PasswordResetCompleteRequestSchema, db: AsyncSession = Depends(get_db)
):
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
    try:
        payload = jwt_manager.decode_refresh_token(data.refresh_token)
        user_id = int(payload.get("sub"))
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired refresh token: {str(e)}")

    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        new_access_token = jwt_manager.create_access_token({"sub": str(user.id)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")

    return TokenRefreshResponseSchema(access_token=new_access_token)
