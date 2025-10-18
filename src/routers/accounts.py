from datetime import timedelta, timezone, datetime
from typing import cast, Optional

from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from config.dependencies import get_accounts_email_notificator
from config.settings import BASE_URL, API_VERSION_PREFIX

from config import get_jwt_auth_manager, get_settings, BaseAppSettings
from database import get_db
from database.models.accounts import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
)
from notifications import EmailSenderInterface
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
    AccountsErrorSchema,
    ChangePasswordRequestSchema,
    ChangeUserRoleRequestSchema,
    BaseEmailSchema,
)
from exceptions.security import BaseSecurityError
from security.dependencies import get_current_user, AdminUser
from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from security.passwords import hash_password


router = APIRouter()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=201,
    responses={
        409: {
            "model": AccountsErrorSchema,
            "description": "A user with the same email already exists.",
        },
        500: {
            "model": AccountsErrorSchema,
            "description": "An error occurred during user creation.",
        },
    },
)
async def user_register(
    background_tasks: BackgroundTasks,
    user: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=409, detail=f"A user with this email {user.email} already exists."
        )

    user_group_stmt = select(UserGroupModel.id).where(UserGroupModel.name == UserGroupEnum.USER)
    user_group_id = await db.scalar(user_group_stmt)
    try:
        new_user = UserModel.create(
            email=user.email, raw_password=user.password, group_id=user_group_id
        )
        db.add(new_user)
        await db.flush()

        user_token = ActivationTokenModel(user=new_user)
        db.add(user_token)

        await db.commit()
        await db.refresh(new_user)
        await db.refresh(user_token)

    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred during user creation.")

    activation_link = f"{BASE_URL}{API_VERSION_PREFIX}/accounts/activate/?token={user_token.token}&email={user.email}"
    background_tasks.add_task(email_sender.send_activation_email, user.email, activation_link)

    return UserRegistrationResponseSchema.model_validate(new_user)


@router.post(
    "/activate/",
    response_model=MessageResponseSchema,
    responses={
        400: {
            "model": AccountsErrorSchema,
            "description": (
                "Invalid or expired activation token, " "or user account is already active."
            ),
        },
        500: {
            "model": AccountsErrorSchema,
            "description": "Failed to activate user due to a database error.",
        },
    },
)
async def activate_user(
    background_tasks: BackgroundTasks,
    data: UserActivationRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):
    db_user = await get_user_by_email(db, data.email)
    if not db_user or db_user.is_active:
        raise HTTPException(
            status_code=400, detail="User account is already active or does not exist."
        )

    stmt_token = select(ActivationTokenModel).where(ActivationTokenModel.user_id == db_user.id)
    db_token = await db.scalar(stmt_token)

    if (
        not db_token
        or db_token.token != data.token
        or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired activation token.")

    db_user.is_active = True
    try:
        await db.delete(db_token)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to activate user due to a database error."
        )

    login_link = f"{BASE_URL}{API_VERSION_PREFIX}/accounts/login/"
    background_tasks.add_task(
        email_sender.send_activation_complete_email,
        str(data.email),
        login_link,
    )

    return MessageResponseSchema.model_validate({"message": "User account activated successfully."})


@router.post(
    "/resend-activation/",
    response_model=MessageResponseSchema,
    responses={
        404: {
            "description": "Not Found - User with this email does not exist.",
            "content": {"application/json": {"example": {"detail": "User not found."}}},
        },
    },
)
async def resend_activation_email(
    background_tasks: BackgroundTasks,
    email_data: BaseEmailSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
) -> MessageResponseSchema:
    stmt = select(UserModel).where(UserModel.email == email_data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.is_active:
        return MessageResponseSchema(message="User account is already active.")

    stmt = select(ActivationTokenModel).where(ActivationTokenModel.user_id == user.id)
    result = await db.execute(stmt)
    expired_tokens = result.scalars().all()

    for expired_token in expired_tokens:
        await db.delete(expired_token)
        await db.commit()

    new_token = ActivationTokenModel(user_id=user.id)
    db.add(new_token)
    await db.commit()

    activation_link = f"{BASE_URL}{API_VERSION_PREFIX}/accounts/activate/?token={new_token.token}&email={user.email}"
    background_tasks.add_task(email_sender.send_activation_email, user.email, activation_link)

    return MessageResponseSchema(message="A new activation email has been sent.")


@router.post(
    "/password-reset/request/",
    response_model=MessageResponseSchema,
)
async def password_reset_token_request(
    background_tasks: BackgroundTasks,
    data: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):
    db_user = await get_user_by_email(db, data.email)

    if db_user and db_user.is_active:
        try:
            stmt_delete_token = delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.user_id == db_user.id
            )
            await db.execute(stmt_delete_token)

            token = PasswordResetTokenModel(user=db_user)
            db.add(token)
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()

        password_reset_complete_link = (
            f"{BASE_URL}{API_VERSION_PREFIX}/accounts/password-reset-complete/?token={token.token}"
        )
        background_tasks.add_task(
            email_sender.send_password_reset_email,
            str(data.email),
            password_reset_complete_link,
        )

    return MessageResponseSchema.model_validate(
        {"message": "If you are registered, you will receive an email with instructions."}
    )


@router.post(
    "/reset-password/complete/",
    response_model=MessageResponseSchema,
    responses={
        400: {"model": AccountsErrorSchema, "description": "Invalid email or token."},
        500: {
            "model": AccountsErrorSchema,
            "description": "An error occurred while resetting the password.",
        },
    },
)
async def password_reset_token_completion(
    background_tasks: BackgroundTasks,
    data: PasswordResetCompleteRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):
    db_user = await get_user_by_email(db, data.email)

    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=400, detail="Invalid email or token.")

    stmt_token = select(PasswordResetTokenModel).where(
        PasswordResetTokenModel.user_id == db_user.id
    )
    db_token = await db.scalar(stmt_token)

    if (
        not db_token
        or db_token.token != data.token
        or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        if db_token:
            await db.delete(db_token)
            await db.commit()
        raise HTTPException(status_code=400, detail="Invalid email or token.")

    try:
        db_user.password = data.password
        await db.commit()

        login_link = f"{BASE_URL}{API_VERSION_PREFIX}/accounts/login/"
        background_tasks.add_task(
            email_sender.send_password_reset_complete_email,
            str(data.email),
            login_link,
        )
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="An error occurred while resetting the password."
        )

    await db.delete(db_token)
    await db.commit()

    return MessageResponseSchema(message="Password reset successfully.")


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    status_code=201,
    responses={
        401: {"model": AccountsErrorSchema, "description": "Invalid email or password."},
        403: {"model": AccountsErrorSchema, "description": "User account is not activated."},
        500: {
            "model": AccountsErrorSchema,
            "description": "An error occurred while processing the request.",
        },
    },
)
async def login_user(
    data: UserLoginRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    settings: BaseAppSettings = Depends(get_settings),
):
    db_user = await get_user_by_email(db, data.email)

    if not db_user or not db_user.verify_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="User account is not activated.")

    payload = {"user_id": db_user.id}
    access_token = jwt_manager.create_access_token(payload)
    refresh_token = jwt_manager.create_refresh_token(payload)

    try:
        db_refresh_token = RefreshTokenModel.create(
            user_id=db_user.id, days_valid=settings.LOGIN_TIME_DAYS, token=refresh_token
        )
        db.add(db_refresh_token)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="An error occurred while processing the request."
        )

    return UserLoginResponseSchema(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/logout/",
    response_model=MessageResponseSchema,
    responses={
        401: {"model": AccountsErrorSchema, "description": "Invalid or missing refresh token."},
        500: {"model": AccountsErrorSchema, "description": "Database error occurred."},
    },
)
async def logout_user(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt_token = select(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
    db_token = await db.scalar(stmt_token)

    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid or missing refresh token.")

    try:
        await db.delete(db_token)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    return MessageResponseSchema(message="User logged out successfully.")


@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
    responses={
        400: {"model": AccountsErrorSchema, "description": "Token has expired."},
        401: {"model": AccountsErrorSchema, "description": "Refresh token not found."},
        404: {"model": AccountsErrorSchema, "description": "User not found."},
    },
)
async def refresh_token(
    data: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
):
    try:
        refresh_payload = jwt_manager.decode_refresh_token(data.refresh_token)
    except BaseSecurityError:
        raise HTTPException(status_code=400, detail="Token has expired.")

    stmt_token = select(RefreshTokenModel).where(RefreshTokenModel.token == data.refresh_token)
    db_token = await db.scalar(stmt_token)
    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token not found.")

    stmt_user = select(UserModel).where(UserModel.id == refresh_payload.get("user_id"))
    db_user = await db.scalar(stmt_user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")

    payload = {"user_id": db_user.id}
    new_access_token = jwt_manager.create_access_token(payload)

    return TokenRefreshResponseSchema(access_token=new_access_token)


@router.post("/change-password/", response_model=MessageResponseSchema)
async def change_password(
    data: ChangePasswordRequestSchema,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    if not current_user.verify_password(data.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect.",
        )

    current_user.password = data.new_password
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the password.",
        )

    return MessageResponseSchema(message="Password changed successfully.")


@router.post("/change-role/", response_model=MessageResponseSchema)
async def change_user_role(
    data: ChangeUserRoleRequestSchema,
    admin: AdminUser = None,
    db: AsyncSession = Depends(get_db),
):
    user_stmt = select(UserModel).where(UserModel.id == data.user_id)
    user = await db.scalar(user_stmt)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot change your role."
        )

    role_stmt = select(UserGroupModel).where(UserGroupModel.name == data.new_role)
    role = await db.scalar(role_stmt)

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    try:
        user.group_id = role.id
        await db.commit()
        await db.refresh(user)

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the user's role.",
        )

    return MessageResponseSchema(message="User role has been successfully changed.")
