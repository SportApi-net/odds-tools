"""Run the shared test vectors (also used by the JavaScript package)."""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import pytest

import odds_tools
from odds_tools import OddsError

from .conftest import VECTORS, load_vectors, vector_cases

CASES = vector_cases()
TOLERANCE = load_vectors()["tolerance"] if VECTORS.exists() else 1e-9
SPECIAL = {"NaN": math.nan, "Infinity": math.inf, "-Infinity": -math.inf}


def decode(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {"$number"}:
        return SPECIAL[value["$number"]]
    if isinstance(value, list):
        return [decode(v) for v in value]
    return value


def normalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: normalize(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    return value


def assert_close(actual: Any, expected: Any, path: str = "result") -> None:
    if isinstance(expected, bool):
        assert actual is expected, f"{path}: {actual!r} != {expected!r}"
    elif isinstance(expected, (int, float)):
        assert isinstance(actual, (int, float)) and not isinstance(actual, bool), path
        bound = TOLERANCE * max(1.0, abs(expected))
        assert abs(actual - expected) <= bound, f"{path}: {actual!r} != {expected!r}"
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), (
            f"{path}: {actual!r} != {expected!r}"
        )
        for i, (a, e) in enumerate(zip(actual, expected)):
            assert_close(a, e, f"{path}[{i}]")
    elif isinstance(expected, dict):
        assert isinstance(actual, dict) and set(actual) == set(expected), (
            f"{path}: keys {sorted(actual)} != {sorted(expected)}"
        )
        for key, e in expected.items():
            assert_close(actual[key], e, f"{path}.{key}")
    else:
        assert actual == expected, f"{path}: {actual!r} != {expected!r}"


def case_id(case: Any) -> str:
    return f"{case['fn']}{case['args']!r}"[:90]


@pytest.mark.skipif(not CASES, reason="shared test vectors not found (repo checkout needed)")
@pytest.mark.parametrize("case", CASES, ids=[case_id(c) for c in CASES])
def test_vector(case: Any) -> None:
    fn = getattr(odds_tools, case["fn"])
    args = decode(case["args"])
    if case.get("error"):
        with pytest.raises(OddsError):
            fn(*args)
    else:
        assert_close(normalize(fn(*args)), case["expected"])


def test_every_public_function_has_vectors() -> None:
    if not CASES:
        pytest.skip("shared test vectors not found")
    covered = {case["fn"] for case in CASES}
    public = {
        name
        for name in odds_tools.__all__
        if callable(getattr(odds_tools, name)) and name[0].islower()
    }
    assert public - covered == set()
