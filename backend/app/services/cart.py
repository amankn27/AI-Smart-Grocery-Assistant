"""In-memory cart store for Phase 0.

Cart state is kept per ``session_id`` in process memory — adequate for the single-instance
demo footprint (brief §2). Persisting carts + user history to Postgres is a Phase 1 item;
the interface here (add/update/remove/summary) is what a DB-backed repository will implement,
so routers won't change when that swap happens.

Totals are delegated to the pure functions in :mod:`app.services.billing`.
"""

from __future__ import annotations

from threading import Lock

from app.services.billing import LineItem, summarize_cart


class CartStore:
    def __init__(self) -> None:
        self._carts: dict[str, dict[str, LineItem]] = {}
        self._lock = Lock()

    def _cart(self, session_id: str) -> dict[str, LineItem]:
        return self._carts.setdefault(session_id, {})

    def add(self, session_id: str, item: LineItem) -> None:
        with self._lock:
            cart = self._cart(session_id)
            existing = cart.get(item.product_id)
            qty = (existing.quantity if existing else 0) + item.quantity
            cart[item.product_id] = LineItem(
                product_id=item.product_id,
                name=item.name,
                mrp=item.mrp,
                quantity=qty,
                category=item.category,
            )

    def update_quantity(self, session_id: str, product_id: str, quantity: int) -> None:
        with self._lock:
            cart = self._cart(session_id)
            if product_id not in cart:
                return
            if quantity <= 0:
                del cart[product_id]
                return
            old = cart[product_id]
            cart[product_id] = LineItem(
                product_id=old.product_id, name=old.name, mrp=old.mrp, quantity=quantity, category=old.category
            )

    def remove(self, session_id: str, product_id: str) -> None:
        with self._lock:
            self._cart(session_id).pop(product_id, None)

    def items(self, session_id: str) -> list[LineItem]:
        return list(self._cart(session_id).values())

    def summary(self, session_id: str):
        return summarize_cart(self.items(session_id))


# Module-level singleton used by the router.
cart_store = CartStore()
