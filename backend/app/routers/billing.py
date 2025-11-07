from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/products")
async def get_products():
    """Billing placeholder - returns stub products."""
    products = [
        {"id": "basic", "name": "Basic Pack", "price": 9.99},
        {"id": "premium", "name": "Premium Pack", "price": 19.99},
    ]
    return {"ok": True, "data": products}


@router.post("/purchase")
async def purchase():
    """Billing placeholder - returns stub order."""
    return {"ok": True, "data": {"order_id": "stub_order", "status": "pending"}}
