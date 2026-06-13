#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_properties.py -- randomized property, edge, and tamper tests for openunit.

These tests use `random` with a FIXED seed, in the TEST PROCESS ONLY. The engine
(`openunit.py`) imports no `random`/`time`/`datetime` and is never modified; the
determinism guard that enforces that scans the engine source alone, so these
randomized tests cannot weaken it (see `test_guard_is_scoped_to_engine`).

What is asserted is the engine's REAL behavior, observed empirically -- not an
idealized version:
  - `population_share` and `realized_weight_at_pin` sum to 1, and
    `baseline_value_usd` equals 1, only up to a tiny rounding residual at
    precision 50 (curated vintages land on an exact 1; arbitrary baskets carry a
    residual of order 1e-50). The determinism guard already uses the same
    tolerance approach (prec 60, tol 1e-30).
  - Negative per-entry populations are NOT rejected as long as the basket total
    stays > 0; only a non-positive TOTAL (and non-positive FX) is rejected. That
    is a current-behavior fact, frozen here rather than wished away.

Standalone (`python3 test_properties.py`) and pytest compatible.
"""

import copy
import json
import random
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

import openunit
import verify_independent

SEED = 20260613
N_BASKETS = 200
N_TAMPER = 50

# Tolerance for the "sums to 1" invariants, evaluated at high precision. The
# engine computes at prec 50, so an arbitrary basket carries a residual of order
# 1e-50; 1e-40 is comfortably above that and far below any meaningful weight.
TOL = Decimal("1e-40")


def _rng():
    return random.Random(SEED)


def _rand_decimal_string(rng, lo_exp, hi_exp):
    """A positive exact-decimal string with random magnitude and digits."""
    digits = rng.choice("123456789") + "".join(
        rng.choice("0123456789") for _ in range(rng.randint(0, 12)))
    exp = rng.randint(lo_exp, hi_exp)
    return str(Decimal(digits).scaleb(exp - len(digits) + 1))


def _rand_spec(rng):
    n = rng.randint(1, 10)
    basket = []
    for i in range(n):
        basket.append({
            "code": "C%02d" % i,
            "name": "通貨%dé—%s" % (i, rng.choice("αβγ世界")),
            "population": str(rng.randint(1, 2_000_000_000)),
            "fx_baseline_usd_per_unit": _rand_decimal_string(rng, -4, 3),
            "fx_valuation_usd_per_unit": _rand_decimal_string(rng, -4, 3),
        })
    return {
        "method": "openunit", "method_version": "v0", "numeraire": "USD",
        "weight_vintage": {"label": "property-test", "basis": "population_share"},
        "basket": basket,
    }


def test_build_is_byte_identical_and_self_verifies():
    """Two builds of the same random spec are byte-identical and verify True."""
    rng = _rng()
    for _ in range(N_BASKETS):
        spec = _rand_spec(rng)
        a1 = openunit.build_artifact(spec)
        a2 = openunit.build_artifact(copy.deepcopy(spec))
        assert json.dumps(a1, sort_keys=True) == json.dumps(a2, sort_keys=True)
        assert a1["artifact_hash"] == a2["artifact_hash"]
        assert openunit.verify_artifact(a1, spec) is True


def test_weight_and_baseline_invariants_within_tolerance():
    """No multiplier => realized_weight_at_pin == population_share (to rounding),
    population shares sum to 1, and baseline_value_usd == 1 (to rounding)."""
    rng = _rng()
    for _ in range(N_BASKETS):
        spec = _rand_spec(rng)
        art = openunit.build_artifact(spec)
        with localcontext() as ctx:
            ctx.prec = 60
            ctx.rounding = ROUND_HALF_EVEN
            share_sum = Decimal(0)
            pin_sum = Decimal(0)
            for row in art["basket"]:
                assert "weight_multiplier" not in row
                assert "effective_weight" not in row
                share = Decimal(row["population_share"])
                pin = Decimal(row["realized_weight_at_pin"])
                assert abs(pin - share) < TOL
                share_sum += share
                pin_sum += pin
            assert abs(share_sum - 1) < TOL
            assert abs(pin_sum - 1) < TOL
            assert abs(Decimal(art["baseline_value_usd"]) - 1) < TOL


def test_value_matches_independent_recompute():
    """value_usd, and every other field, equal an independent Decimal
    recomputation byte-for-byte (the second implementation in
    verify_independent.py, which never imports the engine)."""
    rng = _rng()
    for _ in range(N_BASKETS):
        spec = _rand_spec(rng)
        art = openunit.build_artifact(spec)
        assert verify_independent.recompute_artifact(spec) == art
        assert verify_independent.compare(spec, art) == []


def test_single_character_mutation_breaks_verification():
    """Flipping one character of the serialized artifact (keeping it valid JSON)
    must make verification fail -- both the engine's and the independent one's."""
    rng = _rng()
    checked = 0
    attempts = 0
    while checked < N_TAMPER and attempts < N_TAMPER * 200:
        attempts += 1
        spec = _rand_spec(rng)
        art = openunit.build_artifact(spec)
        text = json.dumps(art, ensure_ascii=False)
        pos = rng.randrange(len(text))
        orig = text[pos]
        repl = rng.choice("0123456789")
        if repl == orig:
            continue
        mutated = text[:pos] + repl + text[pos + 1:]
        if mutated == text:
            continue
        try:
            bad = json.loads(mutated)
        except ValueError:
            continue          # not valid JSON after the flip -- skip
        if not isinstance(bad, dict) or bad == art:
            continue
        checked += 1
        assert openunit.verify_artifact(bad, spec) is False, \
            "engine accepted a 1-char mutation: pos=%d %r->%r" % (pos, orig, repl)
        assert verify_independent.compare(spec, bad) != [], \
            "independent verifier accepted a 1-char mutation"
    assert checked == N_TAMPER, "only produced %d valid mutations" % checked


def test_canonical_key_order_invariance_and_basket_order_sensitivity():
    """input_digest is invariant to dict key order (canonical sorts keys) but
    DOES change when the basket array order changes (array order is identity)."""
    rng = _rng()
    for _ in range(50):
        spec = _rand_spec(rng)
        base = openunit.sha256(spec)

        def reorder_keys(obj):
            if isinstance(obj, dict):
                return {k: reorder_keys(obj[k]) for k in reversed(list(obj))}
            if isinstance(obj, list):
                return [reorder_keys(x) for x in obj]
            return obj

        assert openunit.sha256(reorder_keys(spec)) == base, \
            "digest changed under key reordering -- not canonical"

        if len(spec["basket"]) >= 2:
            shuffled = copy.deepcopy(spec)
            shuffled["basket"].reverse()
            assert openunit.sha256(shuffled) != base, \
                "digest unchanged under basket reordering -- order must matter"


def test_non_positive_total_population_and_fx_are_rejected():
    """Current engine contract, frozen: a non-positive TOTAL population, and any
    non-positive FX rate, raise ValueError. (Per-entry negative population with a
    positive total is intentionally NOT covered here -- see the next test.)"""
    def spec(basket):
        return {"method": "openunit", "method_version": "v0",
                "weight_vintage": {"label": "e", "basis": "population_share"},
                "basket": basket}

    def entry(pop, fxb="1.0", fxv="1.0"):
        return {"code": "A", "population": pop,
                "fx_baseline_usd_per_unit": fxb, "fx_valuation_usd_per_unit": fxv}

    rejecting = [
        [entry("0")],                              # total population 0
        [entry("-100"), entry("100")],             # total cancels to 0
        [entry("100", fxb="0")],                   # fx_baseline 0
        [entry("100", fxb="-1.0")],                # fx_baseline negative
        [entry("100", fxv="0")],                   # fx_valuation 0
        [entry("100", fxv="-1.0")],                # fx_valuation negative
    ]
    for basket in rejecting:
        try:
            openunit.build_artifact(spec(basket))
        except ValueError:
            continue
        raise AssertionError("expected ValueError for basket %r" % basket)


def test_negative_population_with_positive_total_is_currently_accepted():
    """Honest characterization test: the engine does NOT reject a negative
    per-entry population as long as the basket total stays > 0. This freezes
    current behavior (it is not an endorsement); if the engine ever starts
    rejecting negative populations, this test should be updated deliberately."""
    spec = {"method": "openunit", "method_version": "v0",
            "weight_vintage": {"label": "e", "basis": "population_share"},
            "basket": [
                {"code": "A", "population": "-50",
                 "fx_baseline_usd_per_unit": "1.0",
                 "fx_valuation_usd_per_unit": "1.0"},
                {"code": "B", "population": "100",
                 "fx_baseline_usd_per_unit": "1.0",
                 "fx_valuation_usd_per_unit": "1.0"}]}
    art = openunit.build_artifact(spec)            # must not raise
    assert openunit.verify_artifact(art, spec) is True
    # share is population_i / total with a negative numerator -> a negative share
    shares = {r["code"]: Decimal(r["population_share"]) for r in art["basket"]}
    assert shares["A"] < 0 and shares["B"] > 1


def test_guard_is_scoped_to_engine_not_tests():
    """The determinism guard's wall-clock scan targets the ENGINE source only,
    so this test file importing `random` cannot trip it. Verify the guard still
    passes and that its scan reads `openunit` (not this module)."""
    import inspect
    import test_determinism_guard as guard

    # the engine genuinely does not import random, which is why the guard's scan
    # of the engine source stays clean:
    assert "import random" not in inspect.getsource(openunit)

    # this very test module DOES import random -- proving the guard is not
    # scanning test files (or it would be flagging a legitimate dependency):
    with open(__file__, "r", encoding="utf-8") as fh:
        assert "import random" in fh.read()

    guard.test_no_wall_clock_read()                # still passes


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS  " + t.__name__)
        except AssertionError as exc:
            failed += 1
            print("FAIL  %s: %s" % (t.__name__, exc))
    print("-" * 50)
    print("%d/%d PASS" % (len(tests) - failed, len(tests)))
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(1 if _run() else 0)
