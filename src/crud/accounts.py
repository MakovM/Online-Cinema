from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database.models.accounts import UserModel, UserProfileModel
from security.passwords import hash_password


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[UserModel]:
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_user(db: AsyncSession, email: str, raw_password: str, group_id: int) -> UserModel:
    user = UserModel.create(email=email, raw_password=raw_password, group_id=group_id)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except:
        await db.rollback()
        raise
    return user

async def update_user_email(db: AsyncSession, user: UserModel, new_email: str) -> UserModel:
    user.email = new_email
    try:
        await db.commit()
        await db.refresh(user)
    except:
        await db.rollback()
        raise
    return user

async def update_user_password(db: AsyncSession, user: UserModel, new_password: str) -> UserModel:
    user.password = new_password
    try:
        await db.commit()
        await db.refresh(user)
    except:
        await db.rollback()
        raise
    return user

async def deactivate_user(db: AsyncSession, user: UserModel) -> UserModel:
    user.is_active = False
    try:
        await db.commit()
        await db.refresh(user)
    except:
        await db.rollback()
        raise
    return user

async def activate_user(db: AsyncSession, user: UserModel) -> UserModel:
    user.is_active = True
    try:
        await db.commit()
        await db.refresh(user)
    except:
        await db.rollback()
        raise
    return user

async def delete_user(db: AsyncSession, user: UserModel) -> None:
    try:
        await db.delete(user)
        await db.commit()
    except:
        await db.rollback()
        raise
