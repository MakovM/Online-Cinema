from fastapi import FastAPI
from fastapi_pagination import add_pagination

from routers import accounts, movies, orders, carts, profiles, comments, payments

app = FastAPI(title="Cinema Api", description="Description of project")
add_pagination(app)

api_version_prefix = "/api/v1"
app.include_router(accounts.router, prefix=f"{api_version_prefix}/accounts", tags=["Accounts"])
app.include_router(profiles.router, prefix=f"{api_version_prefix}/profiles", tags=["Profiles"])
app.include_router(movies.router, prefix=f"{api_version_prefix}/movies", tags=["Movies"])
app.include_router(comments.router, prefix=f"{api_version_prefix}/comments", tags=["Comments"])
app.include_router(
    carts.router, prefix=f"{api_version_prefix}/shopping-carts", tags=["Shopping Carts"]
)
app.include_router(orders.router, prefix=f"{api_version_prefix}/orders", tags=["Orders"])
app.include_router(payments.router, prefix=f"{api_version_prefix}/payments", tags=["Payments"])
