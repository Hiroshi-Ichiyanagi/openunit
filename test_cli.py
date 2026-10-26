#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_cli.py -- exercises the CLI surface end to end via cli.main(argv).

Standalone (`python3 test_cli.py`) and pytest compatible.
"""

import os
import io
import json
import tempfile
from contextlib import redirect_stdout

import cli
import worldyard
import verify_independent

HERE = os.path.dirname(os.path.abspath(__file__))
# PPP vintages keep the hashed numeraire "USD" but are read in international
# dollars (SPEC.md section 2.3); nominal vintages are read in USD.
PPP_VINTAGES = ("v0.2-ppp-2026-05-15", "v0.4-ppp-unwpp-2026-05-15")
NOMINAL_VINTAGES = ("v0.1-2026-05-15", "v0.3-unwpp-2026-05-15")


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


def _out(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert cli.main(argv) == 0
    return buf.getvalue()


def test_ppp_vintages_print_international_dollars():
    """Display only: `show` and `build` print a PPP vintage's value in
    international $, a nominal one in USD; the artifact (and its hashed
    `numeraire` "USD") is unchanged."""
    with tempfile.TemporaryDirectory() as d:
        for vid in PPP_VINTAGES + NOMINAL_VINTAGES:
            vd = os.path.join(HERE, "data", vid)
            art_p = os.path.join(vd, "artifact.json")
            spec_p = os.path.join(vd, "spec.json")
            with open(art_p, "r", encoding="utf-8") as fh:
                art = json.load(fh)
            with open(spec_p, "r", encoding="utf-8") as fh:
                spec = json.load(fh)
            assert art["numeraire"] == "USD", vid
            shown = _out(["show", art_p])
            out_p = os.path.join(d, vid + ".json")
            built = _out(["build", spec_p, "-o", out_p])
            with open(out_p, "r", encoding="utf-8") as fh:
                assert json.load(fh) == art, vid
            ppp = vid in PPP_VINTAGES
            for text in (shown, built):
                assert ("international $ (numeraire field: USD)" in text) == ppp, vid
            assert worldyard._ppp_valued(spec) == ppp, vid
            assert verify_independent.is_ppp_valued(spec) == ppp, vid
            assert (worldyard.display_unit(art)
                    == worldyard.display_unit(art, spec)), vid


def test_display_unit_needs_a_ppp_valuation_leg():
    """A spec that records PPP factors but values at other rates is not
    printed as international $; neither is the plain test spec."""
    art = worldyard.build_artifact(SPEC)
    assert worldyard.display_unit(art, SPEC) == "USD"
    assert worldyard.display_unit(art) == "USD"
    spec = json.loads(json.dumps(SPEC))
    for e in spec["basket"]:
        e["ppp_factor_lcu_per_intl_usd"] = "2"
    assert not worldyard._ppp_valued(spec)
    assert not verify_independent.is_ppp_valued(spec)
    for e in spec["basket"]:
        e["fx_valuation_usd_per_unit"] = "0.5"
    assert worldyard._ppp_valued(spec)
    assert verify_independent.is_ppp_valued(spec)


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
