"""Cart endpoints. All money math is delegated to the deterministic billing core."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Query

from app.schemas.models import (
    CartAddRequest,
    CartItemOut,
    CartResponse,
    CartUpdateRequest,
)
from app.services.billing import LineItem
from app.services.cart import cart_store

router = APIRouter(prefix="/cart", tags=["cart"])

DEFAULT_SESSION = "demo"


def _build_response(session_id: str) -> CartResponse:
    items = cart_store.items(session_id)
    summary = cart_store.summary(session_id)
    return CartResponse(
        session_id=session_id,
        items=[
            CartItemOut(
                product_id=i.product_id,
                name=i.name,
                mrp=float(i.mrp),
                quantity=i.quantity,
                category=i.category,
                line_total=f"{i.line_total:.2f}",
            )
            for i in items
        ],
        **{k: (v if isinstance(v, int) else str(v)) for k, v in summary.as_dict().items()},
    )


@router.get("", response_model=CartResponse)
def get_cart(session_id: str = Query(DEFAULT_SESSION)) -> CartResponse:
    return _build_response(session_id)


@router.post("/add", response_model=CartResponse)
def add_to_cart(req: CartAddRequest, session_id: str = Query(DEFAULT_SESSION)) -> CartResponse:
    cart_store.add(
        session_id,
        LineItem(
            product_id=req.product_id,
            name=req.name,
            mrp=Decimal(str(req.mrp)),
            quantity=req.quantity,
            category=req.category,
        ),
    )
    return _build_response(session_id)


@router.post("/update", response_model=CartResponse)
def update_cart(req: CartUpdateRequest, session_id: str = Query(DEFAULT_SESSION)) -> CartResponse:
    cart_store.update_quantity(session_id, req.product_id, req.quantity)
    return _build_response(session_id)


@router.post("/remove", response_model=CartResponse)
def remove_from_cart(product_id: str, session_id: str = Query(DEFAULT_SESSION)) -> CartResponse:
    cart_store.remove(session_id, product_id)
    return _build_response(session_id)
