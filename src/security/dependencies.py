from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.dependencies import get_jwt_auth_manager
from database import get_db
from database.models.accounts import UserModel, UserGroupEnum

from database.models.accounts import UserModel
from exceptions import TokenExpiredError, InvalidTokenError



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/login/")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    jwt_manager=Depends(get_jwt_auth_manager),
) -> UserModel:
    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except (TokenExpiredError, InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
        )
    user_stmt = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(selectinload(UserModel.group))
    )
    user = await db.scalar(user_stmt)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    return user


def require_role(*allowed_roles: UserGroupEnum):
    async def check_role(
        current_user: UserModel = Depends(get_current_user),
    ) -> UserModel:
        if not any(current_user.has_group(role) for role in allowed_roles):
            roles_str = ", ".join(role.value for role in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {roles_str}",
            )
        return current_user

    return check_role


CurrentUser = Annotated[UserModel, Depends(get_current_user)]
ModerUser = Annotated[UserModel, Depends(require_role(UserGroupEnum.MODERATOR))]
AdminUser = Annotated[UserModel, Depends(require_role(UserGroupEnum.ADMIN))]
ModerAdminUser = Annotated[
    UserModel,
    Depends(
        require_role(
            UserGroupEnum.ADMIN,
            UserGroupEnum.MODERATOR,
        )
    ),
]
