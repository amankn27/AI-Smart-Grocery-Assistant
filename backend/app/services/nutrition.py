"""Turn raw OCR text of a nutrition panel into a structured, confidence-flagged object.

This is the *deterministic edge cleanup* between the probabilistic OCR step and the rest
of the app. OCR gives us noisy lines like ``"Enery 480 kcal"`` or ``"Protien : 7.2g"``;
this module normalizes label spelling, extracts the numeric value + unit, and attaches a
per-field confidence so downstream code (and the UI) can decide when to ask the user to
confirm (brief §3, graceful degradation).

No model or network calls — pure text in, structured object out. Tested in
``tests/test_nutrition.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Canonical fields we try to extract, each with the label variants/misspellings OCR
# commonly produces and the unit we normalize the value to. Hindi (Devanagari) label terms
# are included so bilingual Indian packaging parses too (Phase 3 multi-language OCR).
_FIELD_SYNONYMS: dict[str, tuple[str, ...]] = {
    "energy_kcal": ("energy", "enery", "calories", "calorie", "energ", "kcal", "ऊर्जा"),
    "protein_g": ("protein", "protien", "proteins", "प्रोटीन"),
    "fat_g": ("total fat", "fat", "fats", "total fa", "कुल वसा", "वसा"),
    "saturated_fat_g": ("saturated fat", "sat fat", "saturates", "saturated", "संतृप्त वसा"),
    "carbohydrate_g": ("carbohydrate", "carbohydrates", "carbs", "carbohydrat",
                       "total carbohydrate", "कार्बोहाइड्रेट"),
    "sugar_g": ("sugar", "sugars", "total sugar", "of which sugars", "शर्करा", "चीनी", "शक्कर"),
    "fiber_g": ("fiber", "fibre", "dietary fiber", "dietary fibre", "फाइबर", "रेशा"),
    "sodium_mg": ("sodium", "sodum", "salt", "सोडियम", "नमक"),
}

# Devanagari digits → ASCII, so values printed in Hindi numerals parse.
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# Fields whose canonical unit is grams vs milligrams vs kcal.
_UNIT_OF: dict[str, str] = {
    "energy_kcal": "kcal",
    "protein_g": "g",
    "fat_g": "g",
    "saturated_fat_g": "g",
    "carbohydrate_g": "g",
    "sugar_g": "g",
    "fiber_g": "g",
    "sodium_mg": "mg",
}

# Number possibly with a decimal; tolerate OCR using ',' as decimal separator.
_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)")
# Trailing unit token right after the number, if present.
_UNIT_TOKEN = re.compile(r"(kcal|kj|mg|g|mcg|µg|%)", re.IGNORECASE)


@dataclass
class Field:
    """One extracted nutrition value with the confidence we place in it (0..1)."""

    value: Optional[float]
    unit: Optional[str]
    confidence: float
    raw: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.value is not None and self.confidence >= 0.5


@dataclass
class NutritionFacts:
    """Structured, per-100g (or per-serving) nutrition with confidence per field."""

    fields: dict[str, Field] = field(default_factory=dict)
    basis: str = "unknown"  # "per_100g" | "per_serving" | "unknown"

    def get(self, name: str) -> Optional[float]:
        f = self.fields.get(name)
        return f.value if f and f.ok else None

    @property
    def low_confidence_fields(self) -> list[str]:
        return [name for name, f in self.fields.items() if not f.ok]

    def as_dict(self) -> dict:
        return {
            "basis": self.basis,
            "fields": {
                name: {"value": f.value, "unit": f.unit, "confidence": round(f.confidence, 2)}
                for name, f in self.fields.items()
            },
            "low_confidence_fields": self.low_confidence_fields,
        }


def _normalize_number(token: str) -> Optional[float]:
    try:
        return float(token.translate(_DEVANAGARI_DIGITS).replace(",", "."))
    except ValueError:
        return None


def detect_script(text: str) -> str:
    """Cheap language hint: 'hi' if Devanagari is present, else 'en'."""
    for ch in text:
        if "ऀ" <= ch <= "ॿ":
            return "hi"
    return "en"


def _detect_basis(text: str) -> str:
    low = text.lower()
    if "per 100" in low or "/100" in low or "per100" in low:
        return "per_100g"
    if "per serv" in low or "serving" in low or "per pack" in low:
        return "per_serving"
    return "unknown"


def _convert_to_canonical(canonical_field: str, value: float, unit: Optional[str]) -> tuple[float, str]:
    """Coerce a parsed value to the canonical unit (e.g. salt g → sodium mg heuristics)."""
    target = _UNIT_OF[canonical_field]
    if unit is None:
        return value, target
    unit = unit.lower()
    if canonical_field == "sodium_mg":
        # Label often lists "salt" in grams; sodium ≈ salt(g) * 400 mg. If already mg, keep.
        if unit == "g":
            return round(value * 400.0, 1), "mg"
        return value, "mg"
    if canonical_field == "energy_kcal" and unit == "kj":
        return round(value / 4.184, 1), "kcal"
    if target == "g" and unit == "mg":
        return round(value / 1000.0, 3), "g"
    return value, target


def parse_nutrition(ocr_text: str) -> NutritionFacts:
    """Parse raw multi-line OCR text into :class:`NutritionFacts`.

    Confidence heuristic: a field scores high (0.9) when its label matched exactly and a
    number+unit were found on the same line; medium (0.6) when the label was a fuzzy/
    misspelled variant; low (0.3) when a number was found but the unit was missing/odd.
    Fields never seen are simply absent (callers treat absent as "ask the user").
    """
    facts = NutritionFacts(basis=_detect_basis(ocr_text))
    lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]

    for canonical_field, synonyms in _FIELD_SYNONYMS.items():
        best: Optional[Field] = None
        for line in lines:
            low = line.lower()
            matched_variant = next((s for s in synonyms if s in low), None)
            if matched_variant is None:
                continue

            num_match = _NUMBER.search(line, low.find(matched_variant))
            if not num_match:
                # Try any number on the line as a weaker signal.
                num_match = _NUMBER.search(line)
            if not num_match:
                continue

            value = _normalize_number(num_match.group(1))
            if value is None:
                continue

            unit_match = _UNIT_TOKEN.search(line, num_match.end())
            unit = unit_match.group(1) if unit_match else None

            # Confidence: exact canonical label token present → high, else fuzzy → medium.
            exact = matched_variant == synonyms[0]
            if unit is not None and exact:
                confidence = 0.9
            elif unit is not None:
                confidence = 0.7
            elif exact:
                confidence = 0.5
            else:
                confidence = 0.3

            value, canonical_unit = _convert_to_canonical(canonical_field, value, unit)
            candidate = Field(value=value, unit=canonical_unit, confidence=confidence, raw=line)
            if best is None or candidate.confidence > best.confidence:
                best = candidate

        if best is not None:
            facts.fields[canonical_field] = best

    return facts
