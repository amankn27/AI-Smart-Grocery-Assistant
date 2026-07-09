"""Deterministic health scoring for a product's per-100g nutrition.

Produces a 0..100 score, a letter grade, and a list of human-readable warnings, judged
against Indian reference daily values and WHO/FSSAI-style thresholds for sugar, sodium,
saturated fat, and fibre/protein. This is intentionally a transparent rule engine (not a
model) so results are explainable and testable — the LLM is only used later to *phrase*
advice, never to compute the score (brief §3).

Tested in ``tests/test_health_scoring.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Reference daily values (adult, indicative) used for the "% of daily" warnings.
RDA = {
    "sugar_g": 50.0,      # WHO: <10% of 2000 kcal ≈ 50 g; ideal <25 g
    "sodium_mg": 2000.0,  # WHO <2 g sodium/day
    "saturated_fat_g": 20.0,
    "fiber_g": 30.0,
    "protein_g": 55.0,
}

# Per-100g thresholds (UK FSA "traffic light" style, adapted). (low_max, high_min)
_TRAFFIC = {
    "fat_g": (3.0, 17.5),
    "saturated_fat_g": (1.5, 5.0),
    "sugar_g": (5.0, 22.5),
    "sodium_mg": (120.0, 600.0),
}

Severity = str  # "green" | "amber" | "red"


@dataclass
class Warning:
    field: str
    severity: Severity
    message: str


@dataclass
class HealthResult:
    score: int                       # 0 (worst) .. 100 (best)
    grade: str                       # A..E
    warnings: list[Warning] = field(default_factory=list)
    positives: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "grade": self.grade,
            "warnings": [{"field": w.field, "severity": w.severity, "message": w.message} for w in self.warnings],
            "positives": self.positives,
        }


def _traffic_severity(field_name: str, value: float) -> Severity:
    low_max, high_min = _TRAFFIC[field_name]
    if value <= low_max:
        return "green"
    if value >= high_min:
        return "red"
    return "amber"


def _grade_for(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "E"


def score_nutrition(
    *,
    energy_kcal: Optional[float] = None,
    protein_g: Optional[float] = None,
    fat_g: Optional[float] = None,
    saturated_fat_g: Optional[float] = None,
    carbohydrate_g: Optional[float] = None,
    sugar_g: Optional[float] = None,
    fiber_g: Optional[float] = None,
    sodium_mg: Optional[float] = None,
) -> HealthResult:
    """Score per-100g nutrition. ``None`` fields are skipped (neither reward nor penalty).

    Starts at 100 and subtracts penalties for red/amber sugar, sodium, and saturated fat;
    adds small bonuses for protein and fibre. Clamped to 0..100.
    """
    score = 100.0
    warnings: list[Warning] = []
    positives: list[str] = []

    # --- Penalties: sugar, sodium, saturated fat (traffic-light driven) ---
    for name, value in (
        ("sugar_g", sugar_g),
        ("sodium_mg", sodium_mg),
        ("saturated_fat_g", saturated_fat_g),
        ("fat_g", fat_g),
    ):
        if value is None:
            continue
        sev = _traffic_severity(name, value)
        if sev == "red":
            score -= 22
            warnings.append(Warning(name, "red", f"High {name.replace('_', ' ')}: {value:g} per 100g"))
        elif sev == "amber":
            score -= 8
            warnings.append(Warning(name, "amber", f"Moderate {name.replace('_', ' ')}: {value:g} per 100g"))

    # --- Energy density penalty ---
    if energy_kcal is not None and energy_kcal >= 450:
        score -= 8
        warnings.append(Warning("energy_kcal", "amber", f"Calorie-dense: {energy_kcal:g} kcal per 100g"))

    # --- Bonuses: protein, fibre ---
    if protein_g is not None and protein_g >= 8:
        score += 8
        positives.append(f"Good protein source ({protein_g:g} g per 100g)")
    if fiber_g is not None and fiber_g >= 6:
        score += 8
        positives.append(f"High in fibre ({fiber_g:g} g per 100g)")
    elif fiber_g is not None and fiber_g >= 3:
        score += 3
        positives.append(f"Contains fibre ({fiber_g:g} g per 100g)")

    score_int = max(0, min(100, round(score)))
    return HealthResult(score=score_int, grade=_grade_for(score_int), warnings=warnings, positives=positives)
