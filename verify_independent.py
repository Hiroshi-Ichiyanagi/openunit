#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_independent.py -- an INDEPENDENT second implementation of the openunit
verification procedure.

This verifier is written from the published documents alone -- `SPEC.md`
(method, formulas, verification rules) and `ARTIFACT_FORMAT.md` (byte-level
canonical encoding, hashing, field layout). It deliberately does NOT import
`openunit`, `cli`, or `anchor`, and shares no code with them: if the engine
were wrong, subtly non-deterministic, or tampered with, this program would
disagree with its output. Standard library only (json, hashlib, decimal, sys,
argparse).

Usage:
    python3 verify_independent.py <spec.json> <artifact.json>

It re-derives, from the spec alone: every population share, effective weight,
fixed amount, the baseline value, the valuation value, both realized-weight
columns, the conditional multiplier fields, `input_digest`, and
`artifact_hash`. It then compares the fully recomputed artifact against the
published one, field by field.

Exit status:
    0   the published artifact matches the independent recomputation exactly
        (every field, both hashes)
    1   verification failed; each differing field is listed on stdout
    2   operational error (unreadable file, invalid JSON, malformed spec)

> Don't trust me. Verify me.  -- so here is the second pair of eyes.
"""

import argparse
import hashlib
import json
import sys
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

# ARTIFACT_FORMAT.md section 1: exact decimal arithmetic, precision 50,
# ROUND_HALF_EVEN, inside a context that does not leak to the caller.
DEC_PRECISION = 50


# --- canonical bytes & hashing (ARTIFACT_FORMAT.md sections 2-3) -------------
def canonical_bytes(value):
    """UTF-8 bytes of json.dumps(value, sort_keys=True, separators=(",", ":"),
    ensure_ascii=False) -- the only encoding ever hashed."""
    text = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return text.encode("utf-8")


def hash_of(value):
    """Lowercase-hex SHA-256 over the canonical bytes, 'sha256:'-prefixed."""
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


# --- independent recomputation (SPEC.md sections 2.1-2.2, format sec 6-7) ----
def recompute_artifact(spec):
    """Derive the complete expected artifact from the spec, using only the
    published formulas:

        effective_weight_i = (population_i * m_i) / sum_j(population_j * m_j)
        population_share_i = population_i / sum_j(population_j)
        amount_i           = effective_weight_i / fx_baseline_i
        baseline_value     = sum_i(amount_i * fx_baseline_i)    (= 1)
        value              = sum_i(amount_i * fx_valuation_i)
        realized@pin_i     = amount_i * fx_baseline_i / baseline_value
        realized@val_i     = amount_i * fx_valuation_i / value

    The two multiplier fields are emitted only when at least one basket entry
    carries `weight_multiplier` (the backward-compatibility rule).
    """
    entries = spec["basket"]
    multipliers_present = any("weight_multiplier" in e for e in entries)

    with localcontext() as ctx:
        ctx.prec = DEC_PRECISION
        ctx.rounding = ROUND_HALF_EVEN

        headcount = Decimal(0)
        weighted_headcount = Decimal(0)
        for e in entries:
            p = Decimal(e["population"])
            if p < 0:
                raise ValueError("population must be >= 0 for %r" % e.get("code"))
            headcount += p
            weighted_headcount += p * Decimal(e.get("weight_multiplier", "1"))
        if headcount <= 0 or weighted_headcount <= 0:
            raise ValueError(
                "spec basket has non-positive total population / effective weight")

        per_entry = []
        baseline_total = Decimal(0)
        valuation_total = Decimal(0)
        for e in entries:
            p = Decimal(e["population"])
            m = Decimal(e.get("weight_multiplier", "1"))
            rate_pin = Decimal(e["fx_baseline_usd_per_unit"])
            rate_val = Decimal(e["fx_valuation_usd_per_unit"])
            if rate_pin <= 0 or rate_val <= 0:
                raise ValueError("non-positive FX rate in spec entry %r"
                                 % e.get("code"))
            share = p / headcount
            eff = (p * m) / weighted_headcount
            qty = eff / rate_pin
            at_pin = qty * rate_pin
            at_val = qty * rate_val
            baseline_total += at_pin
            valuation_total += at_val
            per_entry.append((e, m, share, eff, qty, at_pin, at_val))

        rows = []
        for (e, m, share, eff, qty, at_pin, at_val) in per_entry:
            row = {
                "code": e["code"],
                "name": e.get("name", e["code"]),
                "population_share": str(share),
                "fixed_amount": str(qty),
                "realized_weight_at_pin": str(at_pin / baseline_total),
                "realized_weight_at_valuation": str(at_val / valuation_total),
            }
            if multipliers_present:
                row["weight_multiplier"] = str(m)
                row["effective_weight"] = str(eff)
            rows.append(row)

        body = {
            "method": "openunit",
            "method_version": spec.get("method_version", "v0"),
            "numeraire": spec.get("numeraire", "USD"),
            "weight_vintage_label": spec["weight_vintage"]["label"],
            "weight_basis": spec["weight_vintage"]["basis"],
            "baseline_value_usd": str(baseline_total),
            "value_usd": str(valuation_total),
            "basket": rows,
            "input_digest": hash_of(spec),
        }
        expected = dict(body)
        expected["artifact_hash"] = hash_of(body)
        return expected


# --- field-by-field comparison ------------------------------------------------
def _walk_diffs(expected, published, path, out):
    """Collect every (path, expected, published) difference between the two
    JSON values, recursing into objects and arrays."""
    if isinstance(expected, dict) and isinstance(published, dict):
        for key in sorted(set(expected) | set(published)):
            here = "%s.%s" % (path, key) if path else key
            if key not in published:
                out.append((here, expected[key], "<missing>"))
            elif key not in expected:
                out.append((here, "<unexpected>", published[key]))
            else:
                _walk_diffs(expected[key], published[key], here, out)
    elif isinstance(expected, list) and isinstance(published, list):
        if len(expected) != len(published):
            out.append((path + ".length", len(expected), len(published)))
        for i, (a, b) in enumerate(zip(expected, published)):
            _walk_diffs(a, b, "%s[%d]" % (path, i), out)
    elif expected != published:
        out.append((path, expected, published))


def compare(spec, artifact):
    """Return the list of differences between the independent recomputation
    and the published artifact. Empty list == verified."""
    diffs = []
    expected = recompute_artifact(spec)

    # SPEC.md section 5, condition 1: the artifact must be paired with this spec.
    if artifact.get("input_digest") != expected["input_digest"]:
        diffs.append(("input_digest (sha256 of canonical spec)",
                      expected["input_digest"], artifact.get("input_digest")))

    # SPEC.md section 5, condition 2: internal integrity of the published file
    # (hash of the published artifact minus its own artifact_hash key).
    claimed = {k: v for k, v in artifact.items() if k != "artifact_hash"}
    if hash_of(claimed) != artifact.get("artifact_hash"):
        diffs.append(("artifact_hash (internal integrity)",
                      hash_of(claimed), artifact.get("artifact_hash")))

    # SPEC.md section 5, condition 3: full reproduction, every field.
    _walk_diffs(expected, artifact, "", diffs)

    # de-duplicate while preserving order (a tampered hash can trip two checks)
    seen, unique = set(), []
    for d in diffs:
        k = repr(d)
        if k not in seen:
            seen.add(k)
            unique.append(d)
    return unique


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="verify_independent.py",
        description="Independently re-verify an openunit artifact against its "
                    "spec, from the published format documents alone (no "
                    "engine import). Exit 0 iff every field matches.")
    parser.add_argument("spec", help="path to spec.json (the hashed input)")
    parser.add_argument("artifact", help="path to artifact.json (the published "
                                         "result)")
    args = parser.parse_args(argv)

    try:
        with open(args.spec, "r", encoding="utf-8") as fh:
            spec = json.load(fh)
        with open(args.artifact, "r", encoding="utf-8") as fh:
            artifact = json.load(fh)
        diffs = compare(spec, artifact)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: %s" % exc)
        return 2

    if diffs:
        print("INDEPENDENT VERIFICATION: FAIL  (%d field(s) differ)"
              % len(diffs))
        for where, want, got in diffs:
            print("  field    : %s" % where)
            print("    expected : %s" % (want,))
            print("    published: %s" % (got,))
        return 1

    print("INDEPENDENT VERIFICATION: PASS")
    print("  spec          : %s" % args.spec)
    print("  artifact      : %s" % args.artifact)
    print("  input_digest  : %s" % artifact["input_digest"])
    print("  artifact_hash : %s" % artifact["artifact_hash"])
    print("  value_usd     : %s %s" % (artifact["value_usd"],
                                       artifact["numeraire"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
