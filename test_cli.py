#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_cli.py -- exercises the CLI surface end to end via cli.main(argv).

Standalone (`python3 test_cli.py`) and pytest compatible.
"""

import os
import json
import tempfile
import cli


SPEC = {
    "method": "openunit", "method_version": "v0", "numeraire": "USD",
    "weight_vintage": {"label": "test", "basis": "population_share"},
    "basket": [
        {"code": "USD", "name": "United States", "population": "150",
         "fx_baseline_usd_per_unit": "1.0", "fx_valuation_usd_per_unit": "1.0"},
        {"code": "INR", "name": "India", "population": "300",
         "fx_baseline_usd_per_unit": "0.0104", "fx_valuation_usd_per_unit": "0.0103"},
    ],
}


def _write(d, name, obj):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    return p


def test_build_then_verify():
    with tempfile.TemporaryDirectory() as d:
        spec_p = _write(d, "spec.json", SPEC)
        art_p = os.path.join(d, "artifact.json")
        assert cli.main(["build", spec_p, "-o", art_p]) == 0
        assert cli.main(["verify", art_p, spec_p]) == 0


def test_verify_detects_tamper():
    with tempfile.TemporaryDirectory() as d:
        spec_p = _write(d, "spec.json", SPEC)
        art_p = os.path.join(d, "artifact.json")
        assert cli.main(["build", spec_p, "-o", art_p]) == 0
        with open(art_p, "r", encoding="utf-8") as fh:
            art = json.load(fh)
        art["value_usd"] = "9.9"  # tamper
        with open(art_p, "w", encoding="utf-8") as fh:
            json.dump(art, fh)
        assert cli.main(["verify", art_p, spec_p]) == 1


def test_show_runs():
    with tempfile.TemporaryDirectory() as d:
        spec_p = _write(d, "spec.json", SPEC)
        art_p = os.path.join(d, "artifact.json")
        cli.main(["build", spec_p, "-o", art_p])
        assert cli.main(["show", art_p]) == 0


def test_anchor_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        spec_p = _write(d, "spec.json", SPEC)
        art_p = os.path.join(d, "artifact.json")
        anc_p = os.path.join(d, "anchor.json")
        cli.main(["build", spec_p, "-o", art_p])
        assert cli.main(["anchor", art_p, "-o", anc_p, "--label", "t"]) == 0
        assert cli.main(["verify-anchor", anc_p, art_p]) == 0


def test_anchor_chain_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        spec_p = _write(d, "spec.json", SPEC)
        art_p = os.path.join(d, "artifact.json")
        g_p = os.path.join(d, "g.json")
        n_p = os.path.join(d, "n.json")
        cli.main(["build", spec_p, "-o", art_p])
        cli.main(["anchor", art_p, "-o", g_p])
        assert cli.main(["anchor", art_p, "-o", n_p, "--prev", g_p]) == 0
        assert cli.main(["verify-anchor", n_p, art_p, "--prev", g_p]) == 0


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
