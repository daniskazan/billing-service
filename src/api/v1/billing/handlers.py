from fastapi import APIRouter
from fastapi import Request


billing = APIRouter(
    prefix="/billing",
    tags=["billing"]
)


@billing.get(
    "/operations-history"
)
def get_operations_history(
    request: Request
):
    return None