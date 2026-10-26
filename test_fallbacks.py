#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_fallbacks.py -- the pre-declared data states and fallbacks of SPEC.md
("Data states and fallbacks"), implemented by `openunit.resolve_input`.

Each case uses a real-world situation recorded in SPEC.md:
  - ECB publishes no reference rate on TARGET closing days (stale, max age);
  - the ECB suspended the RUB reference rate after 1 March 2022 (suspended);
  - Bulgaria's lev became EUR at 1.95583 on 2026-01-01 (fixed conversion);
  - a currency with more than one rate on one date (declared selection);
  - BLS published no October 2025 CPI for most series (permanent hole);
  - a series whose publisher stops it (source retirement);
and in every other case the answer is an explicit `unavailable`, never a guess.

Standalone (`python3 test_fallbacks.py`) and pytest compatible.
"""

import copy
import json
import os
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

import openunit

HERE = os.path.dirname(os.path.abspath(__file__))

# ECB USD-per-EUR reference rates around Easter 2026 (Good Friday 2026-04-03,
# Easter Monday 2026-04-06: TARGET closing days). Values are illustrative;
# only the dates matter here.
EUR_USD = {"observations": [
    {"date": "2026-04-01", "value": "1.1501"},
    {"date": "2026-04-02", "value": "1.1502"},
    {"date": "2026-04-07", "value": "1.1507"},
]}


def _raises_value_error(fn, *a, **k):
    try:
        fn(*a, **k)
    except ValueError:
        return True
    return False


# --- ok / stale / too old ----------------------------------------------------
def test_exact_observation_is_ok():
    r = openunit.resolve_input("2026-04-02", EUR_USD, max_age_days=4)
    assert r == {"state": "ok", "value": "1.1502",
                 "observation_date": "2026-04-02", "age_days": "0",
                 "rate_type": None, "flags": [], "reason": None}


def test_closing_day_carries_forward_within_max_age():
    """Easter Monday: Thursday's rate is 4 days old -> 'stale', flagged."""
    r = openunit.resolve_input("2026-04-06", EUR_USD, max_age_days=4)
    assert r["state"] == "stale"
    assert r["value"] == "1.1502"
    assert r["observation_date"] == "2026-04-02"
    assert r["age_days"] == "4"
    assert r["flags"] == ["STALE"]
    assert r["reason"] is None


def test_older_than_max_age_is_unavailable():
    r = openunit.resolve_input("2026-04-06", EUR_USD, max_age_days=3)
    assert r["state"] == "unavailable"
    assert r["value"] is None
    assert r["reason"] == "TOO_OLD"
    # the last observation is still reported, for diagnosis only
    assert r["observation_date"] == "2026-04-02" and r["age_days"] == "4"


def test_no_observation_on_or_before_target_is_unavailable():
    r = openunit.resolve_input("2026-03-31", EUR_USD, max_age_days=4)
    assert r["state"] == "unavailable" and r["reason"] == "NO_OBSERVATION"
    assert r["value"] is None and r["observation_date"] is None


def test_never_uses_a_later_observation():
    """No look-ahead: 2026-04-07 exists but must not serve 2026-04-06."""
    r = openunit.resolve_input("2026-04-06", EUR_USD, max_age_days=4)
    assert r["observation_date"] == "2026-04-02"


# --- suspended / unrepresentative rate ---------------------------------------
RUB = {
    "observations": [{"date": "2022-02-28", "value": "0.00843"},
                     {"date": "2022-03-01", "value": "0.00812"}],
    # the ECB published its last EUR/RUB reference rate on 1 March 2022
    "suspended_since": "2022-03-02",
}


def test_suspended_rate_is_unavailable_even_within_max_age():
    r = openunit.resolve_input("2022-03-02", RUB, max_age_days=4)
    assert r["state"] == "unavailable" and r["reason"] == "SUSPENDED"
    assert r["value"] is None
    r = openunit.resolve_input("2026-05-15", RUB, max_age_days=10000)
    assert r["reason"] == "SUSPENDED"


def test_before_suspension_resolves_normally():
    r = openunit.resolve_input("2022-03-01", RUB, max_age_days=4)
    assert r["state"] == "ok" and r["value"] == "0.00812"


# --- extinct currency, fixed conversion --------------------------------------
BGN = {
    # USD per BGN before the changeover (illustrative values)
    "observations": [{"date": "2025-12-30", "value": "0.5970"},
                     {"date": "2025-12-31", "value": "0.5980"}],
    "fixed_conversion": {
        "effective": "2026-01-01",
        "units_per_successor": "1.95583",     # BGN 1.95583 = EUR 1
        "successor": {"observations": [       # USD per EUR (ECB)
            {"date": "2026-01-09", "value": "1.1642"}]},
    },
}


def test_extinct_currency_uses_fixed_conversion_from_successor():
    r = openunit.resolve_input("2026-01-09", BGN, max_age_days=4)
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        expected = str(Decimal("1.1642") / Decimal("1.95583"))
    assert r["state"] == "fixed_conversion"
    assert r["value"] == expected
    assert r["observation_date"] == "2026-01-09" and r["age_days"] == "0"
    assert r["flags"] == ["FIXED_CONVERSION"]


def test_fixed_conversion_inherits_successor_staleness():
    r = openunit.resolve_input("2026-01-11", BGN, max_age_days=4)   # Sunday
    assert r["state"] == "fixed_conversion"
    assert r["flags"] == ["FIXED_CONVERSION", "STALE"]
    assert r["age_days"] == "2"


def test_fixed_conversion_unavailable_successor_is_unavailable():
    r = openunit.resolve_input("2026-01-08", BGN, max_age_days=4)
    assert r["state"] == "unavailable"
    assert r["reason"] == "SUCCESSOR_UNAVAILABLE:NO_OBSERVATION"
    assert r["value"] is None


def test_before_changeover_uses_own_observations():
    r = openunit.resolve_input("2025-12-31", BGN, max_age_days=4)
    assert r["state"] == "ok" and r["value"] == "0.5980"


def test_no_carry_forward_of_old_currency_across_changeover():
    """2026-01-02 is within 4 days of the last BGN rate, but the lev no
    longer exists: only the fixed conversion may answer (here: no EUR rate
    yet -> unavailable)."""
    r = openunit.resolve_input("2026-01-02", BGN, max_age_days=4)
    assert r["state"] == "unavailable"
    assert r["reason"] == "SUCCESSOR_UNAVAILABLE:NO_OBSERVATION"


# --- multiple official / parallel rates --------------------------------------
TWO_RATES = {"observations": [
    {"date": "2026-05-15", "value": "0.0011", "rate_type": "official"},
    {"date": "2026-05-15", "value": "0.0008", "rate_type": "parallel"},
    {"date": "2026-05-14", "value": "0.0011", "rate_type": "official"},
]}


def test_multiple_rates_without_declared_rule_is_unavailable():
    r = openunit.resolve_input("2026-05-15", TWO_RATES, max_age_days=4)
    assert r["state"] == "unavailable"
    assert r["reason"] == "AMBIGUOUS_MULTIPLE_RATES"
    assert r["value"] is None


def test_multiple_rates_declared_rule_selects_and_flags():
    r = openunit.resolve_input("2026-05-15", TWO_RATES, max_age_days=4,
                               rate_type="official")
    assert r["state"] == "ok" and r["value"] == "0.0011"
    assert r["rate_type"] == "official"
    assert r["flags"] == ["MULTIPLE_RATES"]


def test_declared_rate_type_absent_is_unavailable():
    r = openunit.resolve_input("2026-05-15", TWO_RATES, max_age_days=4,
                               rate_type="tourist")
    assert r["state"] == "unavailable" and r["reason"] == "NO_OBSERVATION"


def test_two_values_of_the_declared_type_on_one_date_is_ambiguous():
    s = copy.deepcopy(TWO_RATES)
    s["observations"].append(
        {"date": "2026-05-15", "value": "0.0012", "rate_type": "official"})
    r = openunit.resolve_input("2026-05-15", s, max_age_days=4,
                               rate_type="official")
    assert r["state"] == "unavailable"
    assert r["reason"] == "AMBIGUOUS_MULTIPLE_RATES"


# --- permanent data hole -----------------------------------------------------
CPI = {   # monthly series: one observation per month, dated the 1st
    "observations": [{"date": "2025-09-01", "value": "324.800"},
                     {"date": "2025-11-01", "value": "324.100"}],
    "permanent_holes": ["2025-10-01"],   # October 2025: never published
}


def test_permanent_hole_is_unavailable_never_interpolated():
    r = openunit.resolve_input("2025-10-01", CPI, max_age_days=62)
    assert r["state"] == "unavailable" and r["reason"] == "PERMANENT_HOLE"
    assert r["value"] is None and r["observation_date"] is None


def test_periods_around_a_hole_resolve():
    assert openunit.resolve_input("2025-09-01", CPI, max_age_days=0)["value"] \
        == "324.800"
    assert openunit.resolve_input("2025-11-01", CPI, max_age_days=0)["value"] \
        == "324.100"


def test_observation_inside_a_declared_hole_is_rejected():
    s = copy.deepcopy(CPI)
    s["observations"].append({"date": "2025-10-01", "value": "324.5"})
    assert _raises_value_error(openunit.resolve_input, "2025-11-01", s,
                               max_age_days=0)


# --- source / endpoint retirement --------------------------------------------
RETIRED = {"observations": [{"date": "2026-11-06", "value": "1.10"}],
           "retired_since": "2026-11-09"}


def test_retired_source_is_unavailable_after_retirement():
    r = openunit.resolve_input("2026-11-09", RETIRED, max_age_days=4)
    assert r["state"] == "unavailable" and r["reason"] == "SOURCE_RETIRED"


def test_retired_source_still_answers_before_retirement():
    r = openunit.resolve_input("2026-11-08", RETIRED, max_age_days=4)
    assert r["state"] == "stale" and r["value"] == "1.10"


# --- determinism, purity, validation ------------------------------------------
def test_pure_and_order_independent():
    s = copy.deepcopy(TWO_RATES)
    before = copy.deepcopy(s)
    a = openunit.resolve_input("2026-05-15", s, max_age_days=4,
                               rate_type="official")
    assert s == before, "resolve_input mutated its input"
    s["observations"].reverse()
    b = openunit.resolve_input("2026-05-15", s, max_age_days=4,
                               rate_type="official")
    assert a == b
    assert json.loads(json.dumps(a)) == a     # plain JSON values only


def test_resolver_reads_no_clock():
    """Same guard as test_determinism_guard.py, for the resolver: it must work
    while time.* is poisoned (the source scan there covers this module)."""
    import time as _time
    saved = {n: getattr(_time, n) for n in ("time", "monotonic", "perf_counter")}

    def boom(*a, **k):
        raise AssertionError("wall-clock was read -- determinism violated")

    try:
        for n in saved:
            setattr(_time, n, boom)
        r = openunit.resolve_input("2026-01-11", BGN, max_age_days=4)
        assert r["state"] == "fixed_conversion"
    finally:
        for n, v in saved.items():
            setattr(_time, n, v)


def test_max_age_accepts_decimal_integer_string():
    a = openunit.resolve_input("2026-04-06", EUR_USD, max_age_days=4)
    b = openunit.resolve_input("2026-04-06", EUR_USD, max_age_days="4")
    assert a == b


def test_invalid_inputs_raise():
    bad_calls = [
        ("2026-02-30", EUR_USD, {}),                     # no such date
        ("2026-4-06", EUR_USD, {}),                      # not YYYY-MM-DD
        ("2026-04-06", EUR_USD, {"max_age_days": -1}),
        ("2026-04-06", EUR_USD, {"max_age_days": 1.5}),
        ("2026-04-06", EUR_USD, {"max_age_days": True}),
        ("2026-04-06", {"observations": [{"date": "2026-04-06",
                                          "value": 1.15}]}, {}),     # float
        ("2026-04-06", {"observations": [{"date": "2026-04-06",
                                          "value": "0"}]}, {}),      # <= 0
        ("2026-04-06", {"observations": [{"date": "2026-04-06",
                                          "value": "NaN"}]}, {}),
        ("2026-04-06", {"observations": []}, {"unknown_rule": 1}),
        ("2026-04-06", {"observations": [], "surprise": 1}, {}),
    ]
    for target, series, kw in bad_calls:
        try:
            openunit.resolve_input(target, series, **kw)
        except (ValueError, TypeError):
            continue
        raise AssertionError("accepted invalid input: %r %r %r"
                             % (target, series, kw))


def test_leap_years_and_month_ends():
    s = {"observations": [{"date": "2024-02-28", "value": "1"}]}
    assert openunit.resolve_input("2024-03-01", s, max_age_days=2)["age_days"] == "2"
    s = {"observations": [{"date": "2100-02-28", "value": "1"}]}  # not leap
    assert openunit.resolve_input("2100-03-01", s, max_age_days=1)["age_days"] == "1"
    assert _raises_value_error(openunit.resolve_input, "2100-02-29", s)
    s = {"observations": [{"date": "2025-12-31", "value": "1"}]}
    assert openunit.resolve_input("2026-01-01", s, max_age_days=1)["state"] == "stale"


def _weekday(date):
    """0 = Monday ... 6 = Sunday (2026-04-06 was a Monday)."""
    return (openunit._days(date) - openunit._days("2026-04-06")) % 7


def _easter(y):
    """Gregorian Easter Sunday (anonymous Gregorian algorithm) as YYYY-MM-DD."""
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return "%04d-%02d-%02d" % (y, month, day)


def test_ecb_max_age_covers_every_target_closing_sequence():
    """With publication on every weekday except TARGET closing days (1 Jan,
    Good Friday, Easter Monday, 1 May, 25-26 Dec), the latest rate on or
    before any calendar day of 2000-2199 is at most 4 days old, and 4 is
    reached -- so DECLARED_MAX_AGE_DAYS for the ECB is the tightest value."""
    closed = set()
    for y in range(1999, 2200):
        e = openunit._days(_easter(y))
        closed |= {e - 2, e + 1}
        for md in ("01-01", "05-01", "12-25", "12-26"):
            closed.add(openunit._days("%04d-%s" % (y, md)))
    start, end = openunit._days("2000-01-01"), openunit._days("2199-12-31")
    monday = openunit._days("2026-04-06")
    last_pub, worst = None, 0
    for n in range(openunit._days("1999-12-01"), end + 1):
        if (n - monday) % 7 < 5 and n not in closed:
            last_pub = n
        if n >= start:
            worst = max(worst, n - last_pub)
    assert worst == openunit.DECLARED_MAX_AGE_DAYS["ECB euro reference rates"] == 4
    assert _easter(2026) == "2026-04-05" and _weekday("2026-04-03") == 4


def test_shipped_vintages_are_within_declared_max_ages():
    """WPP 2024 (released 2024-07-11) for the 2026-01-09 weight date, and
    PA.NUS.PPP 2024 (observation date 2024-07-01) for the v0.2 valuation date
    2026-05-15, both resolve within the pre-declared maximum ages."""
    ages = openunit.DECLARED_MAX_AGE_DAYS
    wpp = {"observations": [{"date": "2024-07-11", "value": "1"}]}
    r = openunit.resolve_input("2026-01-09", wpp,
                               max_age_days=ages["UN World Population Prospects"])
    assert r["state"] == "stale" and r["age_days"] == "547"
    ppp = {"observations": [{"date": "2024-07-01", "value": "20.4219876045922"}]}
    r = openunit.resolve_input("2026-05-15", ppp,
                               max_age_days=ages["World Bank PA.NUS.PPP"])
    assert r["state"] == "stale" and r["age_days"] == "683"


def test_shipped_vintages_resolve_ok_and_are_unchanged():
    """Every shipped real vintage's raw ECB rates, read as observations on
    their pinned dates, resolve 'ok' with max age 0 to the very strings in the
    spec -- the fallback rules change nothing for existing vintages."""
    for vid in ("v0.1-2026-05-15", "v0.3-unwpp-2026-05-15"):
        with open(os.path.join(HERE, "data", vid, "spec.json"),
                  encoding="utf-8") as fh:
            spec = json.load(fh)
        fx = spec["provenance"]["fx"]
        for e in spec["basket"]:
            for leg, date in (("baseline", fx["baseline_date"]),
                              ("valuation", fx["valuation_date"])):
                raw = e["source_eur_per_unit_" + leg]
                series = {"observations": [{"date": date, "value": raw}]}
                r = openunit.resolve_input(date, series, max_age_days=0)
                assert r["state"] == "ok" and r["value"] == raw, (vid, e["code"])


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS  " + t.__name__)
        except Exception as exc:   # noqa: BLE001 -- report every failure kind
            failed += 1
            print("FAIL  %s: %s: %s" % (t.__name__, type(exc).__name__, exc))
    print("-" * 50)
    print("%d/%d PASS" % (len(tests) - failed, len(tests)))
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(1 if _run() else 0)
