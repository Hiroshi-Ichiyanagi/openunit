#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_vintages.py -- the pinned vintages under data/ must reproduce exactly,
the verified v0 sample must keep its historical hash (backward compatibility),
and the v0.1 nominal FX must be the exact quotient of the raw ECB rates.

Standalone (`python3 test_vintages.py`) and pytest compatible.
"""

import os
import json
import glob
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

import openunit

HERE = os.path.dirname(os.path.abspath(__file__))

# The verified v0 sample hash, reproduced cross-machine. Must not regress.
V0_ARTIFACT_HASH = (
    "sha256:433d5e9560f8dcf928c6d2aff9c48ecb9eba558d19fc8eff191056f3f18356bd")
V0_INPUT_DIGEST = (
    "sha256:9e5c721b2131fe92059f05d702668d2bcb428afab3a27b1e79da9e578a1ef055")

# Pinned hashes of the shipped real vintages (post verbatim-ECB normalization,
# 2026-06-13 -- see docs/AUDIT.md addendum). Must match data/ exactly.
VINTAGE_ARTIFACT_HASH = {
    "v0.1-2026-05-15":
        "sha256:1e615cf7cffe025667c98150cfb2010ed368bf838fe3b14fd460b05974839a3a",
    "v0.2-ppp-2026-05-15":
        "sha256:566c95c1753dbcaa70bbfd58c295ced2117d4907d4d7aabb992d68a93f10b97a",
}


def _load(p):
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_v0_sample_backward_compatible():
    spec = _load(os.path.join(HERE, "sample_input.json"))
    art = openunit.build_artifact(spec)
    assert art["input_digest"] == V0_INPUT_DIGEST
    assert art["artifact_hash"] == V0_ARTIFACT_HASH
    assert openunit.verify_artifact(art, spec)


def test_all_vintages_reproduce():
    specs = glob.glob(os.path.join(HERE, "data", "*", "spec.json"))
    assert specs, "no vintages found under data/"
    for spec_p in specs:
        d = os.path.dirname(spec_p)
        spec = _load(spec_p)
        art_disk = _load(os.path.join(d, "artifact.json"))
        art_built = openunit.build_artifact(spec)
        assert art_built == art_disk, "vintage %s does not reproduce" % d
        assert openunit.verify_artifact(art_disk, spec), \
            "vintage %s fails verification" % d


def test_vintage_hashes_are_pinned():
    """Each shipped vintage carries exactly its pinned artifact_hash, and every
    vintage under data/ is covered by a pin (no unpinned vintage ships)."""
    dirs = sorted(os.path.basename(os.path.dirname(p)) for p in
                  glob.glob(os.path.join(HERE, "data", "*", "artifact.json")))
    assert dirs == sorted(VINTAGE_ARTIFACT_HASH), \
        "vintages on disk do not match the pinned set: %s" % dirs
    for vid, expected in VINTAGE_ARTIFACT_HASH.items():
        art = _load(os.path.join(HERE, "data", vid, "artifact.json"))
        assert art["artifact_hash"] == expected, \
            "pinned artifact_hash regressed for %s" % vid


def test_v0_1_fx_is_exact_quotient_of_ecb():
    """Integrity link: derived usd_per_unit == (USD per EUR)/(C per EUR)."""
    matches = glob.glob(os.path.join(HERE, "data", "v0.1-*", "spec.json"))
    assert matches, "v0.1 vintage not found"
    spec = _load(matches[0])
    for e in spec["basket"]:
        if e["code"] in ("USD", "EUR"):
            continue
        with localcontext() as ctx:
            ctx.prec = 50
            ctx.rounding = ROUND_HALF_EVEN
            usd_per_eur_b = Decimal(
                next(x for x in spec["basket"] if x["code"] == "EUR")
                ["fx_baseline_usd_per_unit"])
            expect_b = usd_per_eur_b / Decimal(e["source_eur_per_unit_baseline"])
        assert Decimal(e["fx_baseline_usd_per_unit"]) == expect_b, \
            "FX derivation mismatch for %s" % e["code"]


def test_make_vintages_verify_cli():
    """`make_vintages.py --verify` must report every vintage as reproducing
    (exit 0) without writing to disk."""
    import make_vintages
    assert make_vintages.main(["--verify"]) == 0


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
