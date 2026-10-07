from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VECTORS = Path(__file__).resolve().parents[2] / "test-vectors" / "vectors.json"


def load_vectors() -> dict[str, Any]:
    with VECTORS.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def vector_cases() -> list[dict[str, Any]]:
    if not VECTORS.exists():  # e.g. running from an sdist without the repo
        return []
    cases: list[dict[str, Any]] = load_vectors()["cases"]
    return cases
