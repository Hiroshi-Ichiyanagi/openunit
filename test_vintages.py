#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_vintages.py -- the pinned vintages under data/ must reproduce exactly,
the verified v0 sample must keep its historical hash (backward compatibility),
the v0.1 nominal FX must be the exact quotient of the raw ECB rates, published
vintage files must stay byte-identical, v0.3-unwpp must be exactly the UN
extract on v0.1's FX, and the vintage registry (data/vintages.json) must be
consistent with the specs it describes.

Standalone (`python3 test_vintages.py`) and pytest compatible.
"""

import os
import json
import glob
import hashlib
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
    "v0.3-unwpp-2026-05-15":
        "sha256:63812b17a3a73666fad42ab5e53418e4c376802f2c94b1ca0d306f269aabc04f",
}

# Published vintages are never rewritten (SPEC.md, "Corrections and
# supersession"): the exact bytes of their files are pinned here, so even an
# edit that keeps every hash valid (e.g. a reworded SOURCES.md) fails. The
# OpenTimestamps proofs (*.ots) are deliberately not pinned: they live outside
# every hash and may legitimately be upgraded (docs/ANCHORING.md).
PUBLISHED_FILE_SHA256 = {
    "v0.1-2026-05-15/spec.json":
        "487136a5f038231db4d07f5a296019f2093c0a28de6bb4b3ffdcc5fd0fc142ee",
    "v0.1-2026-05-15/artifact.json":
        "65545e6a441a337ea5f5a6d6c082a557520566f5ed16cd505e3d51697d3e5176",
    "v0.1-2026-05-15/SOURCES.md":
        "0bdd9e4a649048f9153afdc6bbd9db37248556d06f7b4e3c48f1111c257188a0",
    "v0.2-ppp-2026-05-15/spec.json":
        "7cddd69167ede3c17d3a06008551ec2954101bd239226331b83b54cec91b6ced",
    "v0.2-ppp-2026-05-15/artifact.json":
        "dc5577633c261b07f21f047d760f9a8a450eba4dea71970084fd9f559e4bf014",
    "v0.2-ppp-2026-05-15/SOURCES.md":
        "ab7723917f5b9d1342052cd5a7a99bf1976acfdaf45ed8407fff44aab0b95c87",
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


def test_published_vintage_files_are_frozen():
    """v0.1 and v0.2 are published: their files must stay byte-identical."""
    for rel, expected in PUBLISHED_FILE_SHA256.items():
        with open(os.path.join(HERE, "data", rel), "rb") as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
        assert got == expected, "published file %s was modified" % rel


def _v0_3():
    d = os.path.join(HERE, "data", "v0.3-unwpp-2026-05-15")
    return _load(os.path.join(d, "spec.json")), _load(os.path.join(d, "artifact.json"))


def test_v0_3_populations_are_the_un_extract():
    """v0.3-unwpp populations are exactly TPopulation1July x 1000 from the
    committed UN extract, and the euro area is the sum of its 21 members on
    the valuation date (Bulgaria included)."""
    import make_vintages as mv
    un = mv.load_un_extract()
    spec, _ = _v0_3()
    pop = {e["code"]: e["population"] for e in spec["basket"]}
    for code, iso in mv.ISO3_FOR_CCY.items():
        assert pop[code] == un[iso]["population_persons"], code
    members = spec["provenance"]["euro_area"]["members_iso3"]
    assert len(members) == 21 and "BGR" in members
    assert members == sorted(members) and len(set(members)) == 21
    assert int(pop["EUR"]) == sum(int(un[i]["population_persons"]) for i in members)
    for row in un.values():   # every extract value is a whole number of persons
        assert Decimal(row["tpopulation1july_thousands"]) * 1000 == \
            Decimal(row["population_persons"])


def test_v0_3_extract_is_bound_to_the_spec():
    """The spec pins the sha256 of the committed extract (so the extract is
    part of the vintage's identity) and records the raw UN file."""
    spec, _ = _v0_3()
    p = spec["provenance"]["population"]
    with open(os.path.join(HERE, p["extract"]), "rb") as fh:
        assert hashlib.sha256(fh.read()).hexdigest() == p["extract_sha256"]
    assert p["licence"] == "CC BY 3.0 IGO"
    assert p["file"] == "WPP2024_Demographic_Indicators_Medium.csv.gz"
    assert len(p["file_sha256"]) == 64 and int(p["file_bytes"]) > 0


def test_v0_3_fx_is_v0_1_fx():
    """v0.3-unwpp changes population only: every FX input equals v0.1's."""
    spec3, _ = _v0_3()
    spec1 = _load(os.path.join(HERE, "data", "v0.1-2026-05-15", "spec.json"))
    keys = ("fx_baseline_usd_per_unit", "fx_valuation_usd_per_unit",
            "source_eur_per_unit_baseline", "source_eur_per_unit_valuation")
    assert [e["code"] for e in spec3["basket"]] == [e["code"] for e in spec1["basket"]]
    for e3, e1 in zip(spec3["basket"], spec1["basket"]):
        for k in keys:
            assert e3[k] == e1[k], (e3["code"], k)
    fx1 = dict(spec1["provenance"]["fx"])
    fx3 = dict(spec3["provenance"]["fx"])
    assert fx3.pop("same_as") == "v0.1-2026-05-15"
    assert fx3 == fx1


def test_v0_3_supersedes_v0_1():
    """The correction names the exact artifact it supersedes."""
    spec3, _ = _v0_3()
    art1 = _load(os.path.join(HERE, "data", "v0.1-2026-05-15", "artifact.json"))
    (sup,) = spec3["supersedes"]
    assert sup["vintage"] == "v0.1-2026-05-15"
    assert sup["artifact_hash"] == art1["artifact_hash"]
    codes = [r["code"] for r in sup["reasons"]]
    assert codes == ["EURO_AREA_MEMBERSHIP", "POPULATION_VIA_REPUBLISHER",
                     "POPULATION_MISMATCH"]


def test_vintage_registry_is_consistent():
    """data/vintages.json lists every vintage with its artifact_hash; the
    supersedes / superseded_by links are symmetric, match each spec's own
    (hashed) `supersedes` field, and a vintage is 'superseded' iff something
    supersedes it."""
    reg = _load(os.path.join(HERE, "data", "vintages.json"))
    assert reg["format"] == "openunit-vintage-registry-1"
    entries = {v["id"]: v for v in reg["vintages"]}
    assert len(entries) == len(reg["vintages"]), "duplicate registry id"
    on_disk = sorted(os.path.basename(os.path.dirname(p)) for p in
                     glob.glob(os.path.join(HERE, "data", "*", "spec.json")))
    assert sorted(entries) == on_disk
    for vid, e in entries.items():
        d = os.path.join(HERE, "data", vid)
        art = _load(os.path.join(d, "artifact.json"))
        spec = _load(os.path.join(d, "spec.json"))
        assert e["artifact_hash"] == art["artifact_hash"], vid
        assert e["status"] in ("current", "superseded"), vid
        assert (e["status"] == "superseded") == bool(e["superseded_by"]), vid
        assert e["supersedes"] == [s["vintage"] for s in spec.get("supersedes", [])]
        for s in spec.get("supersedes", []):
            assert entries[s["vintage"]]["artifact_hash"] == s["artifact_hash"]
        for old in e["supersedes"]:
            assert vid in entries[old]["superseded_by"], (vid, old)
        for new in e["superseded_by"]:
            assert vid in entries[new]["supersedes"], (vid, new)
        for w in e["warnings"]:
            assert w["code"] == w["code"].upper() and w["detail"], vid


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
