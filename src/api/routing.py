from fastapi import APIRouter

from api.v1.billing.handlers import billing

v1 = APIRouter(
    prefix="/api/v1",
)
v1.include_router(billing)
