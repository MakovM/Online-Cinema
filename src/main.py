from fastapi import FastAPI
from sqlalchemy import select
from database.models.accounts import UserGroupModel, UserGroupEnum
from database.session_postgresql import get_postgresql_db
from routers import accounts, orders, carts

app = FastAPI(title="Cinema Api", description="Description of project")

api_version_prefix = "/api/v1"
app.include_router(accounts.router, prefix=f"{api_version_prefix}/accounts", tags=["Accounts"])
app.include_router(carts.router, prefix=f"{api_version_prefix}/shopping-carts", tags=["Shopping Carts"])

app.include_router(orders.router, prefix=f"{api_version_prefix}/orders", tags=["Orders"])


@app.on_event("startup")
async def create_default_groups():
    async for db in get_postgresql_db():
        for group in UserGroupEnum:
            stmt = select(UserGroupModel).where(UserGroupModel.name == group)
            result = await db.execute(stmt)
            if not result.scalars().first():
                db.add(UserGroupModel(name=group))
        await db.commit()
