#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_ppp.py -- v0.2 PPP mechanism and population x multiplier weighting.

Runs standalone (`python3 test_ppp.py`, nonzero exit on failure) and under
pytest. No I/O, no clock.
"""

from decimal import Decimal
import openunit


def _base_entry(code, pop, fxb, fxv, mult=None):
    e = {"code": code, "name": code, "population": pop,
         "fx_baseline_usd_per_unit": fxb, "fx_valuation_usd_per_unit": fxv}
    if mult is not None:
        e["weight_multiplier"] = mult
    return e


def _spec(basket, version="v0.2"):
    return {
        "method": "openunit", "method_version": version, "numeraire": "USD",
        "weight_vintage": {"label": "test", "basis": "population_share"},
        "basket": basket,
    }


def test_no_multiplier_is_v0_format():
    """A spec with no weight_multiplier must not emit weighting fields."""
    spec = _spec([_base_entry("USD", "100", "1.0", "1.0"),
                  _base_entry("INR", "200", "0.0104", "0.0104")])
    art = openunit.build_artifact(spec)
    for row in art["basket"]:
        assert "weight_multiplier" not in row
        assert "effective_weight" not in row
    assert openunit.verify_artifact(art, spec)


def test_multiplier_changes_effective_weight():
    """population x multiplier must redistribute the pinned (effective) weight,
    while population_share stays the pure headcount share."""
    spec = _spec([_base_entry("USD", "100", "1.0", "1.0", mult="1"),
                  _base_entry("INR", "100", "0.0104", "0.0104", mult="3")])
    art = openunit.build_artifact(spec)
    rows = {r["code"]: r for r in art["basket"]}
    # equal population -> equal population_share
    assert rows["USD"]["population_share"] == rows["INR"]["population_share"]
    # multiplier 1 vs 3 -> effective weights 1/4 and 3/4
    assert Decimal(rows["USD"]["effective_weight"]) == Decimal("0.25")
    assert Decimal(rows["INR"]["effective_weight"]) == Decimal("0.75")
    # pinned realized weight equals the effective weight by construction
    assert (Decimal(rows["INR"]["realized_weight_at_pin"])
            == Decimal(rows["INR"]["effective_weight"]))
    assert openunit.verify_artifact(art, spec)


def test_ppp_valuation_shifts_weight_to_low_price():
    """v0.2 reference shape: population weights, PPP valuation leg. A currency
    whose PPP rate exceeds its nominal rate must gain realized weight at
    valuation (real purchasing power > nominal)."""
    # nominal USD-per-unit on the baseline leg; PPP int-$ per unit on valuation.
    # INR: nominal 0.0104, PPP 1/23.5 = 0.042553...  (PPP >> nominal)
    # USD: 1.0 on both legs.
    spec = _spec([
        _base_entry("USD", "100", "1.0", "1.0"),
        _base_entry("INR", "100", "0.0104", str(Decimal(1) / Decimal("23.5"))),
    ])
    art = openunit.build_artifact(spec)
    rows = {r["code"]: r for r in art["basket"]}
    inr_pin = Decimal(rows["INR"]["realized_weight_at_pin"])
    inr_val = Decimal(rows["INR"]["realized_weight_at_valuation"])
    assert inr_val > inr_pin, "low-price economy should gain real weight at PPP"
    assert openunit.verify_artifact(art, spec)


def test_multiplier_one_matches_plain_shares():
    """Setting every multiplier to 1 yields the same shares as omitting them."""
    plain = _spec([_base_entry("USD", "150", "1.0", "1.0"),
                   _base_entry("EUR", "350", "1.16", "1.16")])
    withone = _spec([_base_entry("USD", "150", "1.0", "1.0", mult="1"),
                     _base_entry("EUR", "350", "1.16", "1.16", mult="1")])
    a, b = openunit.build_artifact(plain), openunit.build_artifact(withone)
    pa = {r["code"]: r["population_share"] for r in a["basket"]}
    pb = {r["code"]: r["effective_weight"] for r in b["basket"]}
    assert pa == pb  # effective weight (mult=1) == population share


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
