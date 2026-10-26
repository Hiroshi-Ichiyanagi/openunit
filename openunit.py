#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
openunit -- reference implementation (engine)

A deterministic, publicly verifiable, population-weighted *unit of account*.
It does not issue money and it does not settle payments. It only *measures*:
given the same pinned inputs, anyone recomputes the same value and the same
hashes, byte for byte.

Method versions
  v0     one person, one vote          weight_i = pop_i / sum(pop)
  v0.1   same method, real pinned data  (UN population + ECB reference FX)
  v0.2   PPP-aware                       see SPEC.md sections 2 and 7

Mechanism (see SPEC.md):
  - one person, one vote : weight_i proportional to population_i (optionally
                           x a per-entry `weight_multiplier`, default 1)
  - frequency separation : weights pinned at a low-frequency vintage; value
                           read from a separate (e.g. daily, or PPP) FX leg
  - vintage pinning      : fixed currency amounts -- the population version of
                           the SDR fixed-basket method

Determinism guarantees:
  - stdlib only (json, hashlib, decimal)
  - exact arithmetic with decimal.Decimal (prec=50, ROUND_HALF_EVEN) inside an
    isolated localcontext; numbers parsed from strings, never from floats
  - never reads the wall clock (no datetime / time)
  - SHA-256 over canonical JSON for input_digest and artifact_hash

Backward compatibility:
  A spec whose basket entries carry no `weight_multiplier` produces output that
  is byte-for-byte identical to openunit v0 (the extra weighting fields are
  emitted only when at least one multiplier is present).

Data states and fallbacks:
  resolve_input(target, series, max_age_days, rate_type) resolves ONE input
  under the pre-declared rules of SPEC.md ("Data states and fallbacks"): ok,
  stale (within a maximum age), fixed_conversion (extinct currency), or an
  explicit unavailable with a reason -- never a guess. It is a pure function,
  separate from build_artifact, so it changes no artifact and no hash.

"Don't trust me. Verify me."
"""

import json
import hashlib
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

PRECISION = 50
ROUNDING = ROUND_HALF_EVEN

METHOD = "openunit"
METHOD_VERSION = "v0"   # default for specs that do not pin their own version


# --- canonicalization & hashing ---------------------------------------------
def canonical(obj):
    """Deterministic JSON encoding used for every hash."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256(obj):
    return "sha256:" + hashlib.sha256(canonical(obj)).hexdigest()


# --- core computation --------------------------------------------------------
def _D(x):
    """Exact Decimal from a string. Never build a Decimal from a float."""
    return Decimal(str(x))


def _compute(spec):
    """Pure function: spec -> (baseline_value, value, rows). No I/O, no clock."""
    basket = spec["basket"]
    use_mult = any("weight_multiplier" in e for e in basket)

    with localcontext() as ctx:
        ctx.prec = PRECISION
        ctx.rounding = ROUNDING

        total_pop = Decimal(0)
        total_eff = Decimal(0)
        for e in basket:
            pop = _D(e["population"])
            mult = _D(e.get("weight_multiplier", "1"))
            if pop < 0:
                raise ValueError("population must be >= 0 for %s" % e.get("code"))
            total_pop += pop
            total_eff += pop * mult
        if total_pop <= 0 or total_eff <= 0:
            raise ValueError("total population (and effective weight) must be > 0")

        baseline_value = Decimal(0)
        valuation_value = Decimal(0)
        tmp = []
        for e in basket:
            pop = _D(e["population"])
            mult = _D(e.get("weight_multiplier", "1"))
            fx_b = _D(e["fx_baseline_usd_per_unit"])
            fx_v = _D(e["fx_valuation_usd_per_unit"])
            if fx_b <= 0 or fx_v <= 0:
                raise ValueError("fx rates must be > 0 for %s" % e.get("code"))

            pop_share = pop / total_pop           # pure population share
            weight = (pop * mult) / total_eff     # effective (pinned) weight
            amount = weight / fx_b                 # fixed quantity pinned at vintage
            contrib_b = amount * fx_b              # == weight, by construction
            contrib_v = amount * fx_v

            baseline_value += contrib_b
            valuation_value += contrib_v
            tmp.append((e, pop_share, mult, weight, amount, contrib_b, contrib_v))

        rows = []
        for (e, pop_share, mult, weight, amount, contrib_b, contrib_v) in tmp:
            row = {
                "code": e["code"],
                "name": e.get("name", e["code"]),
                "population_share": str(pop_share),
                "fixed_amount": str(amount),
                "realized_weight_at_pin": str(contrib_b / baseline_value),
                "realized_weight_at_valuation": str(contrib_v / valuation_value),
            }
            if use_mult:
                # Emitted only when weighting differs from pure population, so
                # that plain v0 specs stay byte-for-byte identical to openunit v0.
                row["weight_multiplier"] = str(mult)
                row["effective_weight"] = str(weight)
            rows.append(row)

        return str(baseline_value), str(valuation_value), rows


# --- public API --------------------------------------------------------------
def build_artifact(spec):
    """Build a deterministic, self-describing artifact from a spec dict."""
    baseline_value_s, value_s, rows = _compute(spec)

    core = {
        "method": METHOD,
        "method_version": spec.get("method_version", METHOD_VERSION),
        "numeraire": spec.get("numeraire", "USD"),
        "weight_vintage_label": spec["weight_vintage"]["label"],
        "weight_basis": spec["weight_vintage"]["basis"],
        "baseline_value_usd": baseline_value_s,   # == 1 by construction
        "value_usd": value_s,                     # 1 openunit in the numeraire
        "basket": rows,
        "input_digest": sha256(spec),
    }
    artifact = dict(core)
    artifact["artifact_hash"] = sha256(core)
    return artifact


def verify_artifact(artifact, spec, explain=False):
    """True iff `artifact` is internally consistent AND reproduces `spec`."""
    reasons = []

    if artifact.get("input_digest") != sha256(spec):
        reasons.append("input_digest does not match spec")

    core = {k: v for k, v in artifact.items() if k != "artifact_hash"}
    if sha256(core) != artifact.get("artifact_hash"):
        reasons.append("artifact_hash does not match artifact content")

    if build_artifact(spec) != artifact:
        reasons.append("artifact does not reproduce from spec")

    ok = not reasons
    if explain and not ok:
        for r in reasons:
            print("  - " + r)
    return ok


# --- data states and fallbacks (SPEC.md, "Data states and fallbacks") --------
# A pure, deterministic resolver for ONE input (e.g. an FX rate) at ONE target
# date, under pre-declared rules. It is not called by build_artifact, so it
# changes no artifact and no hash; a publisher runs it BEFORE building, and an
# input that resolves to "unavailable" must not be put into a spec at all.

# Pre-declared maximum ages (SPEC.md, "Data states and fallbacks"). The
# observation date of an annual series is 1 July of its reference year; that of
# a population revision is the revision's release date.
DECLARED_MAX_AGE_DAYS = {
    "ECB euro reference rates": 4,     # weekends + TARGET closing days
    "UN World Population Prospects": 1461,   # 4 years from the release
    "World Bank PA.NUS.PPP": 1096,     # 3 years from 1 July of the year
}

_SERIES_KEYS = {"observations", "suspended_since", "retired_since",
                "permanent_holes", "fixed_conversion"}
_OBS_KEYS = {"date", "value", "rate_type"}
_FIXED_KEYS = {"effective", "units_per_successor", "successor"}


def _days(date):
    """Strict 'YYYY-MM-DD' (proleptic Gregorian) -> day number. Pure integer
    arithmetic (H. Hinnant's days-from-civil); no calendar library, no clock."""
    if not isinstance(date, str) or len(date) != 10 or date[4] != "-" \
            or date[7] != "-" or not (date[:4] + date[5:7] + date[8:]).isdigit() \
            or not date.isascii():
        raise ValueError("date must be 'YYYY-MM-DD': %r" % (date,))
    y, m, d = int(date[:4]), int(date[5:7]), int(date[8:])
    leap = (y % 4 == 0 and y % 100 != 0) or y % 400 == 0
    mdays = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if y < 1 or not 1 <= m <= 12 or not 1 <= d <= mdays[m - 1]:
        raise ValueError("no such date: %r" % (date,))
    y -= m <= 2
    era = y // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe


def _positive_decimal(s, what):
    """A finite, > 0 Decimal parsed from a STRING (never from a float)."""
    if not isinstance(s, str):
        raise ValueError("%s must be a decimal string, got %r" % (what, s))
    try:
        v = Decimal(s)
    except ArithmeticError:
        raise ValueError("%s is not a decimal: %r" % (what, s))
    if not v.is_finite() or v <= 0:
        raise ValueError("%s must be finite and > 0: %r" % (what, s))
    return v


def _max_age(n):
    if isinstance(n, bool) or not isinstance(n, (int, str)):
        raise ValueError("max_age_days must be an int or a decimal-integer "
                         "string, got %r" % (n,))
    if isinstance(n, str):
        if not (n.isascii() and n.isdigit()):
            raise ValueError("max_age_days must be a non-negative integer: %r"
                             % (n,))
        n = int(n)
    if n < 0:
        raise ValueError("max_age_days must be >= 0: %r" % (n,))
    return n


def _result(state, value=None, date=None, age=None, rate_type=None,
            flags=(), reason=None):
    return {"state": state, "value": value, "observation_date": date,
            "age_days": None if age is None else str(age),
            "rate_type": rate_type, "flags": sorted(set(flags)),
            "reason": reason}


def resolve_input(target, series, max_age_days=0, rate_type=None):
    """Resolve one input at `target` ('YYYY-MM-DD') from `series` under the
    pre-declared rules of SPEC.md ("Data states and fallbacks").

    series = {
      "observations": [{"date": "YYYY-MM-DD", "value": "<decimal string>",
                        "rate_type": "<optional label>"}, ...],
      "suspended_since": "YYYY-MM-DD",        # optional: publisher suspended it
      "retired_since":   "YYYY-MM-DD",        # optional: publisher stopped it
      "permanent_holes": ["YYYY-MM-DD", ...], # optional: never to be published
      "fixed_conversion": {                   # optional: extinct currency
          "effective": "YYYY-MM-DD",
          "units_per_successor": "<decimal string>",  # e.g. BGN per EUR
          "successor": <series of the successor, same numeraire>},
    }

    Rules, applied in this order (the first that applies decides):
      1. fixed_conversion with target >= effective: resolve the successor
         (same max_age_days / rate_type) and divide by units_per_successor;
         state "fixed_conversion", flags FIXED_CONVERSION + the successor's.
      2. target in permanent_holes            -> unavailable PERMANENT_HOLE
      3. target >= suspended_since            -> unavailable SUSPENDED
      4. target >= retired_since              -> unavailable SOURCE_RETIRED
      5. take observations dated <= target (never a later one), restricted to
         rate_type if one is declared; none   -> unavailable NO_OBSERVATION
      6. more than one on the latest date     -> unavailable
         AMBIGUOUS_MULTIPLE_RATES (never averaged, never picked silently);
         flag MULTIPLE_RATES when a declared rate_type resolved a date that
         carries several rates
      7. age = target - that date in days; age > max_age_days -> unavailable
         TOO_OLD; age == 0 -> "ok"; otherwise "stale" (flag STALE).

    Returns {"state", "value", "observation_date", "age_days", "rate_type",
    "flags", "reason"}; "value" is the observation's string verbatim (or the
    exact quotient for a fixed conversion) and None whenever state is
    "unavailable". Pure: no I/O, no clock, inputs never mutated, the result
    does not depend on the order of the observations. Malformed input raises
    ValueError.
    """
    t = _days(target)
    max_age = _max_age(max_age_days)
    if rate_type is not None and not isinstance(rate_type, str):
        raise ValueError("rate_type must be a string or None")
    if not isinstance(series, dict):
        raise ValueError("series must be a dict")
    unknown = set(series) - _SERIES_KEYS
    if unknown:
        raise ValueError("series has unknown keys: %r" % sorted(unknown))

    obs = []
    for o in series.get("observations", []):
        if not isinstance(o, dict) or set(o) - _OBS_KEYS or \
                "date" not in o or "value" not in o:
            raise ValueError("malformed observation: %r" % (o,))
        _positive_decimal(o["value"], "observation value")
        rt = o.get("rate_type")
        if rt is not None and not isinstance(rt, str):
            raise ValueError("rate_type must be a string: %r" % (o,))
        obs.append((_days(o["date"]), o["date"], o["value"], rt))
    holes = set()
    for h in series.get("permanent_holes", []):
        holes.add(_days(h))
    if any(d in holes for d, _, _, _ in obs):
        raise ValueError("an observation is dated inside a declared "
                         "permanent hole")
    suspended = series.get("suspended_since")
    retired = series.get("retired_since")
    suspended = None if suspended is None else _days(suspended)
    retired = None if retired is None else _days(retired)

    fixed = series.get("fixed_conversion")
    if fixed is not None:
        if not isinstance(fixed, dict) or set(fixed) != _FIXED_KEYS:
            raise ValueError("fixed_conversion needs exactly %s"
                             % sorted(_FIXED_KEYS))
        units = _positive_decimal(fixed["units_per_successor"],
                                  "units_per_successor")
        if t >= _days(fixed["effective"]):
            succ = resolve_input(target, fixed["successor"], max_age, rate_type)
            if succ["state"] == "unavailable":
                return _result("unavailable", date=succ["observation_date"],
                               age=succ["age_days"],
                               rate_type=succ["rate_type"],
                               reason="SUCCESSOR_UNAVAILABLE:" + succ["reason"])
            with localcontext() as ctx:
                ctx.prec = PRECISION
                ctx.rounding = ROUNDING
                value = str(Decimal(succ["value"]) / units)
            return _result("fixed_conversion", value, succ["observation_date"],
                           succ["age_days"], succ["rate_type"],
                           list(succ["flags"]) + ["FIXED_CONVERSION"])

    if t in holes:
        return _result("unavailable", reason="PERMANENT_HOLE")
    if suspended is not None and t >= suspended:
        return _result("unavailable", reason="SUSPENDED")
    if retired is not None and t >= retired:
        return _result("unavailable", reason="SOURCE_RETIRED")

    eligible = [o for o in obs if o[0] <= t and
                (rate_type is None or o[3] == rate_type)]
    if not eligible:
        return _result("unavailable", rate_type=rate_type,
                       reason="NO_OBSERVATION")
    latest = max(o[0] for o in eligible)
    same_day = [o for o in eligible if o[0] == latest]
    date = same_day[0][1]
    age = t - latest
    if len(same_day) > 1:
        return _result("unavailable", date=date, age=age, rate_type=rate_type,
                       reason="AMBIGUOUS_MULTIPLE_RATES")
    flags = []
    if sum(1 for o in obs if o[0] == latest) > 1:
        flags.append("MULTIPLE_RATES")
    if age > max_age:
        return _result("unavailable", date=date, age=age, rate_type=rate_type,
                       flags=flags, reason="TOO_OLD")
    if age > 0:
        flags.append("STALE")
    return _result("ok" if age == 0 else "stale", same_day[0][2], date, age,
                   rate_type, flags)


# --- demo --------------------------------------------------------------------
def _demo(path="sample_input.json"):
    with open(path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)

    artifact = build_artifact(spec)
    ok = verify_artifact(artifact, spec, explain=True)

    q = Decimal("0.000001")
    value = Decimal(artifact["value_usd"]).quantize(q)
    has_mult = any("weight_multiplier" in r for r in artifact["basket"])
    print("openunit reference demo  (%s)" % artifact["method_version"])
    print("-" * 62)
    print("1 openunit  = %s %s" % (value, artifact["numeraire"]))
    print("weight basis: %s   vintage: %s"
          % (artifact["weight_basis"], artifact["weight_vintage_label"]))
    print()
    header = "  code   pop.share    realized@pin   realized@val"
    if has_mult:
        header += "    eff.weight"
    print(header)
    rows = sorted(artifact["basket"],
                  key=lambda r: Decimal(r["realized_weight_at_pin"]), reverse=True)
    for r in rows:
        ps = Decimal(r["population_share"]).quantize(q)
        rp = Decimal(r["realized_weight_at_pin"]).quantize(q)
        rv = Decimal(r["realized_weight_at_valuation"]).quantize(q)
        line = "  %-5s  %9s    %12s   %12s" % (r["code"], ps, rp, rv)
        if has_mult:
            ew = Decimal(r["effective_weight"]).quantize(q)
            line += "  %12s" % ew
        print(line)
    print()
    print("input_digest : %s" % artifact["input_digest"])
    print("artifact_hash: %s" % artifact["artifact_hash"])
    print("-" * 62)
    print("verify_artifact(...) -> %s" % ok)


if __name__ == "__main__":
    import sys
    _demo(sys.argv[1] if len(sys.argv) > 1 else "sample_input.json")
