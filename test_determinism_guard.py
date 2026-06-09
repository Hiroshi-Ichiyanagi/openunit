#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Determinism & integrity guard for openunit (v0).

Run directly:   python3 test_determinism_guard.py
Or with pytest: pytest test_determinism_guard.py

Checks:
  1. same input  -> same values AND same hashes (built twice)
  2. wall-clock independence: the source reads no clock, and a build still
     succeeds while time.* is poisoned to raise
  3. tamper detection: any modified artifact fails verify_artifact
  4. pinned realized weights == population shares (the design invariant)

"Don't trust me. Verify me."
"""

import copy
import json
import inspect
from decimal import Decimal, localcontext

import openunit


def load_spec(path="sample_input.json"):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_same_input_same_output():
    spec = load_spec()
    a1 = openunit.build_artifact(spec)
    a2 = openunit.build_artifact(copy.deepcopy(spec))
    assert a1 == a2, "identical input produced different artifacts"
    assert a1["artifact_hash"] == a2["artifact_hash"], "artifact_hash not reproducible"
    assert a1["input_digest"] == a2["input_digest"], "input_digest not reproducible"
    # surviving a JSON round-trip must not change the hashes
    a3 = json.loads(json.dumps(a1))
    assert a3["artifact_hash"] == a1["artifact_hash"], "hash unstable across JSON"
    assert openunit.verify_artifact(a1, spec) is True


def test_no_wall_clock_read():
    # (a) static: the source must not reference the clock at all
    src = inspect.getsource(openunit)
    forbidden = ("import time", "import datetime", "from time", "from datetime",
                 ".now(", ".utcnow(", ".today(", "monotonic", "perf_counter")
    found = [tok for tok in forbidden if tok in src]
    assert not found, "clock references found in openunit source: %s" % found

    # (b) runtime control: poison time.* then a build must still succeed
    import time as _time
    saved = {n: getattr(_time, n) for n in ("time", "monotonic", "perf_counter")}

    def boom(*a, **k):
        raise AssertionError("wall-clock was read -- determinism violated")

    try:
        for n in saved:
            setattr(_time, n, boom)
        spec = load_spec()
        artifact = openunit.build_artifact(spec)
        assert artifact["value_usd"], "build produced no value"
        assert openunit.verify_artifact(artifact, spec) is True
    finally:
        for n, v in saved.items():
            setattr(_time, n, v)


def test_tamper_is_detected():
    spec = load_spec()
    good = openunit.build_artifact(spec)
    assert openunit.verify_artifact(good, spec) is True

    # (a) flip the value, leave the hash -> internal inconsistency
    bad = copy.deepcopy(good)
    bad["value_usd"] = str(Decimal(bad["value_usd"]) + Decimal("0.000001"))
    assert openunit.verify_artifact(bad, spec) is False

    # (b) flip a weight inside the basket
    bad2 = copy.deepcopy(good)
    bad2["basket"][0]["population_share"] = "0.999999"
    assert openunit.verify_artifact(bad2, spec) is False

    # (c) pair the artifact with a different spec
    spec2 = copy.deepcopy(spec)
    spec2["basket"][0]["population"] = str(
        int(spec2["basket"][0]["population"]) + 1)
    assert openunit.verify_artifact(good, spec2) is False


def test_pinned_weights_equal_population_share():
    spec = load_spec()
    artifact = openunit.build_artifact(spec)
    with localcontext() as ctx:
        ctx.prec = 60
        tol = Decimal("1e-30")
        total = Decimal(0)
        for row in artifact["basket"]:
            share = Decimal(row["population_share"])
            pinned = Decimal(row["realized_weight_at_pin"])
            total += share
            assert abs(pinned - share) < tol, (
                "pinned weight != population share for %s" % row["code"])
        assert abs(total - Decimal(1)) < tol, "population shares do not sum to 1"


if __name__ == "__main__":
    import sys
    tests = [
        ("1 same input -> same output", test_same_input_same_output),
        ("2 no wall-clock read",        test_no_wall_clock_read),
        ("3 tamper is detected",        test_tamper_is_detected),
        ("4 pinned weights = shares",   test_pinned_weights_equal_population_share),
    ]
    failed = 0
    for label, fn in tests:
        try:
            fn()
            print("PASS  %s" % label)
        except AssertionError as exc:
            failed += 1
            print("FAIL  %s\n      %s" % (label, exc))
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("ERROR %s\n      %r" % (label, exc))
    n = len(tests)
    print("-" * 50)
    print("%d/%d PASS" % (n - failed, n))
    sys.exit(1 if failed else 0)
