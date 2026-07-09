"""Pydantic request/response models for the API surface (Phase 0)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ nutrition/analyze
class NutritionInput(BaseModel):
    energy_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    carbohydrate_g: Optional[float] = None
    sugar_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class WarningOut(BaseModel):
    field: str
    severity: str
    message: str


class AnalyzeResponse(BaseModel):
    score: int
    grade: str
    warnings: list[WarningOut]
    positives: list[str]


# ------------------------------------------------------------------------------- cart
class CartAddRequest(BaseModel):
    product_id: str
    name: str
    mrp: float = Field(ge=0)
    quantity: int = Field(default=1, ge=1)
    category: Optional[str] = None


class CartUpdateRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=0)


class CartItemOut(BaseModel):
    product_id: str
    name: str
    mrp: float
    quantity: int
    category: Optional[str] = None
    line_total: str


class CartResponse(BaseModel):
    session_id: str
    items: list[CartItemOut]
    subtotal: str
    taxable_value: str
    total_cgst: str
    total_sgst: str
    total_gst: str
    total: str
    item_count: int


# ------------------------------------------------------------------------------- chat
class ChatRequest(BaseModel):
    question: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    answer: str
    provider: str


# ----------------------------------------------------------------------- detect/ocr
class DetectionOut(BaseModel):
    label: str
    confidence: float
    bbox_xyxy: list[float]
    needs_confirmation: bool


class DetectResponse(BaseModel):
    model: str
    width: int
    height: int
    detections: list[DetectionOut]


class OcrResponse(BaseModel):
    engine: str
    text: str
    mean_confidence: float
    nutrition: dict
    language: str = "en"
