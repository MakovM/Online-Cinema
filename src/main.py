from fastapi import FastAPI
from routers import accounts


app = FastAPI(title="Cinema Api", description="Description of project")

api_version_prefix = "/api/v1"

app.include_router(accounts.router, prefix=f"{api_version_prefix}/accounts", tags=["Accounts"])
