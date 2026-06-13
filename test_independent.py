#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_independent.py -- the independent second-implementation verifier
(`verify_independent.py`) must agree with the engine on every shipped input,
and must reject any tampered artifact or mismatched spec.

The point of these tests is CROSS-VALIDATION: artifacts produced by the engine
(`openunit.build_artifact`) are checked by a verifier that never imports the
engine. Agreement here means two independent implementations of SPEC.md /
ARTIFACT_FORMAT.md reproduce identical bytes and hashes.

Standalone (`python3 test_independent.py`) and pytest compatible.
"""

import copy
import glob
import json
import os
import subprocess
import sys
import tempfile

import openunit            # engine: used only to GENERATE artifacts to check
import verify_independent  # the independent verifier under test

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(p):
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _vintage_pairs():
    pairs = []
    for spec_p in sorted(glob.glob(os.path.join(HERE, "data", "*", "spec.json"))):
        d = os.path.dirname(spec_p)
        pairs.append((_load(spec_p), _load(os.path.join(d, "artifact.json")), d))
    return pairs


def _cli(spec, artifact):
    """Run `python3 verify_independent.py spec.json artifact.json` on the two
    in-memory objects; return the CLI exit code."""
    with tempfile.TemporaryDirectory() as tmp:
        sp = os.path.join(tmp, "spec.json")
        ap = os.path.join(tmp, "artifact.json")
        with open(sp, "w", encoding="utf-8") as fh:
            json.dump(spec, fh, ensure_ascii=False)
        with open(ap, "w", encoding="utf-8") as fh:
            json.dump(artifact, fh, ensure_ascii=False)
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, "verify_independent.py"), sp, ap],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.returncode


def test_verifier_never_imports_the_engine():
    """Independence guard: the verifier source must not import or reference
    the engine modules at all."""
    src_path = os.path.join(HERE, "verify_independent.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    for forbidden in ("import openunit", "from openunit",
                      "import cli", "from cli",
                      "import anchor", "from anchor"):
        assert forbidden not in src, \
            "verifier is not independent: found %r" % forbidden


def test_all_vintages_pass_independent_verification():
    pairs = _vintage_pairs()
    assert pairs, "no vintages found under data/"
    for spec, art, d in pairs:
        diffs = verify_independent.compare(spec, art)
        assert diffs == [], "independent verification failed for %s: %s" % (d, diffs)
        assert _cli(spec, art) == 0, "CLI exit nonzero for %s" % d


def test_v0_sample_passes_independent_verification():
    """The engine-built v0 sample artifact must be reproduced by the
    independent implementation (no-multiplier branch)."""
    spec = _load(os.path.join(HERE, "sample_input.json"))
    art = openunit.build_artifact(spec)
    assert verify_independent.compare(spec, art) == []
    assert verify_independent.recompute_artifact(spec) == art
    assert _cli(spec, art) == 0


def test_multiplier_branch_passes_independent_verification():
    """A spec with weight_multiplier entries must reproduce, including the two
    conditionally-emitted fields."""
    spec = {
        "method": "openunit", "method_version": "v0.2", "numeraire": "USD",
        "weight_vintage": {"label": "test", "basis": "population_share"},
        "basket": [
            {"code": "USD", "name": "United States", "population": "100",
             "fx_baseline_usd_per_unit": "1.0",
             "fx_valuation_usd_per_unit": "1.0", "weight_multiplier": "1"},
            {"code": "INR", "name": "India", "population": "100",
             "fx_baseline_usd_per_unit": "0.0104",
             "fx_valuation_usd_per_unit": "0.042553",
             "weight_multiplier": "3"},
        ],
    }
    art = openunit.build_artifact(spec)
    assert any("effective_weight" in r for r in art["basket"])
    assert verify_independent.recompute_artifact(spec) == art
    assert verify_independent.compare(spec, art) == []
    assert _cli(spec, art) == 0


def test_tampered_artifact_fails():
    """Any single-field edit to a published artifact must be rejected."""
    for spec, art, d in _vintage_pairs():
        for mutate in (
            lambda a: a.__setitem__("value_usd", a["value_usd"][:-1] + "9"),
            lambda a: a["basket"][0].__setitem__("population_share", "0.5"),
            lambda a: a.__setitem__("artifact_hash",
                                    a["artifact_hash"][:-4] + "0000"),
        ):
            bad = copy.deepcopy(art)
            mutate(bad)
            if bad == art:        # the mutation must actually change something
                continue
            diffs = verify_independent.compare(spec, bad)
            assert diffs, "tampered artifact accepted for %s" % d
            assert _cli(spec, bad) == 1


def test_tampered_spec_fails():
    """Editing the spec (so input_digest no longer matches) must be rejected,
    even though the artifact itself is internally consistent."""
    for spec, art, d in _vintage_pairs():
        bad_spec = copy.deepcopy(spec)
        bad_spec["basket"][0]["population"] = str(
            int(bad_spec["basket"][0]["population"]) + 1)
        diffs = verify_independent.compare(bad_spec, art)
        assert any("input_digest" in str(x[0]) for x in diffs), \
            "spec tamper not flagged as digest mismatch for %s" % d
        assert _cli(bad_spec, art) == 1


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
    sys.exit(1 if _run() else 0)
