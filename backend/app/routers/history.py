"""/history and /products/save — per-user scan history and saved products (auth required)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.database import get_db
from app.deps import get_current_user
from app.services.health_scoring import score_nutrition

router = APIRouter(tags=["history"])


class ScanIn(BaseModel):
    product_id: str = ""
    name: str = ""
    brand: str = ""
    category: str = ""
    mrp: float = 0.0
    quantity: int = 1
    nutrition: dict[str, float] = {}


@router.post("/history/scan", status_code=201)
def record_scan(scan: ScanIn, user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    from app.db.models import Scan

    health = score_nutrition(**scan.nutrition).score if scan.nutrition else 0
    row = Scan(
        user_id=user.id, product_id=scan.product_id, name=scan.name, brand=scan.brand,
        category=scan.category, mrp=scan.mrp, quantity=scan.quantity, health_score=health,
        energy_kcal=scan.nutrition.get("energy_kcal", 0.0),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "health_score": health}


@router.get("/history")
def get_history(limit: int = 50, user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    from app.db.models import Scan

    rows = (
        db.query(Scan).filter(Scan.user_id == user.id)
        .order_by(Scan.created_at.desc()).limit(limit).all()
    )
    return {
        "scans": [
            {
                "id": r.id, "product_id": r.product_id, "name": r.name, "brand": r.brand,
                "category": r.category, "mrp": r.mrp, "quantity": r.quantity,
                "health_score": r.health_score, "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


class SaveIn(BaseModel):
    product_id: str
    name: str = ""
    note: str = ""


@router.post("/products/save", status_code=201)
def save_product(item: SaveIn, user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    from app.db.models import SavedProduct

    row = SavedProduct(user_id=user.id, product_id=item.product_id, name=item.name, note=item.note)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.get("/products/saved")
def saved_products(user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    from app.db.models import SavedProduct

    rows = db.query(SavedProduct).filter(SavedProduct.user_id == user.id).all()
    return {"saved": [{"id": r.id, "product_id": r.product_id, "name": r.name, "note": r.note} for r in rows]}
