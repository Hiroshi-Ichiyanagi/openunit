#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_compat.py -- the rename from openunit to Worldyard breaks nothing:

  - `import openunit` still works: it warns (DeprecationWarning) and returns
    the worldyard module itself, so every function and constant is the same
    object and every hash is the same;
  - `python3 openunit.py` still runs the demo, and the old `openunit` command
    (cli.main_openunit) still runs every subcommand;
  - the artifact's `method` is copied from the spec: "openunit" (and an
    absent method) and "worldyard" are accepted, anything else is rejected,
    by the engine and by the independent verifier alike;
  - every vintage built before the rename still says "openunit" and still
    rebuilds byte for byte; new vintages say "worldyard".

Standalone (`python3 test_compat.py`) and pytest compatible.
"""

import copy
import glob
import io
import json
import os
import subprocess
import sys
import tempfile
import warnings
from contextlib import redirect_stderr, redirect_stdout

import worldyard
import verify_independent

HERE = os.path.dirname(os.path.abspath(__file__))

SPEC = {
    "method": "worldyard", "method_version": "v0.4", "numeraire": "USD",
    "weight_vintage": {"label": "test", "basis": "population_share"},
    "basket": [
        {"code": "USD", "name": "United States", "population": "150",
         "fx_baseline_usd_per_unit": "1.0", "fx_valuation_usd_per_unit": "1.0"},
        {"code": "INR", "name": "India", "population": "300",
         "fx_baseline_usd_per_unit": "0.0104",
         "fx_valuation_usd_per_unit": "0.0103"},
    ],
}

# Vintages built before the rename keep the old method name (SPEC.md, the
# rename note; ARTIFACT_FORMAT.md section 4).
BEFORE_RENAME = ("v0.1-2026-05-15", "v0.2-ppp-2026-05-15",
                 "v0.3-unwpp-2026-05-15")


def _load(p):
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _fresh_import_openunit():
    """Import the shim afresh (a previous import left the worldyard module in
    sys.modules under the old name) and return (module, warnings)."""
    sys.modules.pop("openunit", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import openunit  # noqa: F401  (the import is what is under test)
    return sys.modules["openunit"], caught


def test_import_openunit_warns_and_is_worldyard():
    mod, caught = _fresh_import_openunit()
    assert mod is worldyard
    deps = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert deps, "import openunit did not warn"
    assert "worldyard" in str(deps[0].message)
    # the warning points at the importer, not at the shim or importlib
    assert os.path.basename(deps[0].filename) == os.path.basename(__file__)


def test_openunit_api_is_the_same_objects():
    mod, _ = _fresh_import_openunit()
    for name in ("build_artifact", "verify_artifact", "resolve_input",
                 "canonical", "sha256", "DECLARED_MAX_AGE_DAYS", "_days"):
        assert getattr(mod, name) is getattr(worldyard, name), name


def test_old_spec_builds_identically_under_both_names():
    """The bundled v0 sample (method "openunit") keeps its pinned hash whether
    it is built through `openunit` or `worldyard`."""
    mod, _ = _fresh_import_openunit()
    spec = _load(os.path.join(HERE, "sample_input.json"))
    a = mod.build_artifact(spec)
    b = worldyard.build_artifact(copy.deepcopy(spec))
    assert a == b and a["method"] == "openunit"
    assert a["artifact_hash"] == ("sha256:433d5e9560f8dcf928c6d2aff9c48ecb9e"
                                  "ba558d19fc8eff191056f3f18356bd")


def test_method_is_copied_from_the_spec():
    art = worldyard.build_artifact(SPEC)
    assert art["method"] == "worldyard"
    old = dict(SPEC, method="openunit")
    assert worldyard.build_artifact(old)["method"] == "openunit"
    absent = {k: v for k, v in SPEC.items() if k != "method"}
    assert worldyard.build_artifact(absent)["method"] == "openunit"
    # the name is hashed, so the two names give different artifacts
    assert art["artifact_hash"] != worldyard.build_artifact(old)["artifact_hash"]
    assert worldyard.verify_artifact(art, SPEC)


def test_unknown_method_is_rejected_by_both_implementations():
    for bad in ("Worldyard", "openunit2", "", None, 1):
        spec = dict(SPEC, method=bad)
        try:
            worldyard.build_artifact(spec)
        except ValueError:
            pass
        else:
            raise AssertionError("engine accepted method %r" % (bad,))
        try:
            verify_independent.recompute_artifact(spec)
        except ValueError:
            pass
        else:
            raise AssertionError("verifier accepted method %r" % (bad,))


def test_independent_verifier_accepts_both_names():
    for name in ("openunit", "worldyard"):
        spec = dict(SPEC, method=name)
        art = worldyard.build_artifact(spec)
        assert verify_independent.compare(spec, art) == []
        bad = dict(art, method="worldyard" if name == "openunit" else "openunit")
        assert verify_independent.compare(spec, bad) != []


def test_vintages_keep_their_method_names():
    specs = sorted(glob.glob(os.path.join(HERE, "data", "*", "spec.json")))
    seen = set()
    for spec_p in specs:
        vid = os.path.basename(os.path.dirname(spec_p))
        spec = _load(spec_p)
        art = _load(os.path.join(os.path.dirname(spec_p), "artifact.json"))
        want = "openunit" if vid in BEFORE_RENAME else "worldyard"
        assert spec["method"] == art["method"] == want, vid
        assert worldyard.build_artifact(spec) == art, vid
        seen.add(vid)
    assert set(BEFORE_RENAME) <= seen


def test_openunit_script_runs_the_demo():
    proc = subprocess.run([sys.executable, os.path.join(HERE, "openunit.py")],
                          cwd=HERE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    assert proc.returncode == 0
    out = proc.stdout.decode("utf-8")
    assert "433d5e9560f8dcf928c6d2aff9c48ecb9eba558d19fc8eff191056f3f18356bd" in out
    assert b"DeprecationWarning" in proc.stderr


def test_openunit_command_alias():
    import cli
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "spec.json")
        ap = os.path.join(d, "artifact.json")
        with open(sp, "w", encoding="utf-8") as fh:
            json.dump(SPEC, fh)
        err, out = io.StringIO(), io.StringIO()
        with redirect_stderr(err), redirect_stdout(out):
            assert cli.main_openunit(["build", sp, "-o", ap]) == 0
            assert cli.main_openunit(["verify", ap, sp]) == 0
        assert "deprecated" in err.getvalue() and "worldyard" in err.getvalue()
        assert "1 worldyard =" in out.getvalue()
        assert cli.main(["verify", ap, sp]) == 0


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
