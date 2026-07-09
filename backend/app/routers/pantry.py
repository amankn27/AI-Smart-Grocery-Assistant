"""/pantry — inventory + expiry tracking with reminders (auth required).

The router does DB I/O; all freshness/reminder logic lives in the pure, tested
:mod:`app.services.pantry`.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.db.database import get_db
from app.deps import get_current_user
from app.services.pantry import list_with_status, reminders

router = APIRouter(prefix="/pantry", tags=["pantry"])


class PantryIn(BaseModel):
    product_id: str = ""
    name: str
    category: str = ""
    quantity: int = 1
    expiry_date: date | None = None
    opened: bool = False


def _rows_as_dicts(rows) -> list[dict]:
    return [
        {"id": r.id, "name": r.name, "category": r.category, "quantity": r.quantity,
         "expiry_date": r.expiry_date}
        for r in rows
    ]


@router.post("", status_code=201)
def add_item(item: PantryIn, user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    from app.db.models import PantryItem

    row = PantryItem(
        user_id=user.id, product_id=item.product_id, name=item.name, category=item.category,
        quantity=item.quantity, expiry_date=item.expiry_date, opened=item.opened,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.get("")
def list_items(user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    from app.db.models import PantryItem

    rows = db.query(PantryItem).filter(PantryItem.user_id == user.id).all()
    views = list_with_status(_rows_as_dicts(rows), date.today())
    return {"items": [v.as_dict() for v in views]}


@router.get("/reminders")
def get_reminders(
    within_days: int = Query(3, ge=0, le=90), user=Depends(get_current_user), db=Depends(get_db)
) -> dict:
    from app.db.models import PantryItem

    rows = db.query(PantryItem).filter(PantryItem.user_id == user.id).all()
    rem = reminders(_rows_as_dicts(rows), date.today(), within_days=within_days)
    return {"within_days": within_days, "reminders": [v.as_dict() for v in rem]}


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, user=Depends(get_current_user), db=Depends(get_db)) -> None:
    from app.db.models import PantryItem

    row = db.get(PantryItem, item_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    db.delete(row)
    db.commit()
