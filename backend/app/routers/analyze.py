"""/analyze — deterministic health scoring of a nutrition object."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.models import AnalyzeResponse, NutritionInput, WarningOut
from app.services.health_scoring import score_nutrition

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(nutrition: NutritionInput) -> AnalyzeResponse:
    result = score_nutrition(**nutrition.model_dump())
    return AnalyzeResponse(
        score=result.score,
        grade=result.grade,
        warnings=[WarningOut(field=w.field, severity=w.severity, message=w.message) for w in result.warnings],
        positives=result.positives,
    )
