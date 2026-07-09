"""/dashboard and /report — analytics over history and a PDF invoice for the current cart."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.db.database import get_db
from app.deps import get_current_user
from app.services.analytics import summarize_scans
from app.services.cart import cart_store
from app.services.invoice import build_invoice_pdf

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    from app.db.models import Scan

    rows = db.query(Scan).filter(Scan.user_id == user.id).all()
    scans = [
        {"mrp": r.mrp, "quantity": r.quantity, "category": r.category,
         "health_score": r.health_score, "energy_kcal": r.energy_kcal}
        for r in rows
    ]
    return summarize_scans(scans)


@router.get("/report")
def report(session_id: str = Query("demo")) -> Response:
    """Cart → PDF invoice. Uses the same GST math as the billing core."""
    items = cart_store.items(session_id)
    pdf = build_invoice_pdf(items)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice-{session_id}.pdf"'},
    )
