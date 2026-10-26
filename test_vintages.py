#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_vintages.py -- the pinned vintages under data/ must reproduce exactly,
the verified v0 sample must keep its historical hash (backward compatibility),
the v0.1 nominal FX must be the exact quotient of the raw ECB rates, published
vintage files must stay byte-identical, v0.3-unwpp must be exactly the UN
extract on v0.1's FX, v0.4-ppp-unwpp must be v0.3's populations on v0.2's FX
with the pinned World Bank PPP response, and the vintage registry
(data/vintages.json) must be consistent with the specs it describes.

Standalone (`python3 test_vintages.py`) and pytest compatible.
"""

import os
import json
import glob
import hashlib
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

import worldyard

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
        "sha256:0fe13c839711bd60c3f87df59c84b47517bbaf4e8141d52dee5d86c42666b7af",
    "v0.4-ppp-unwpp-2026-05-15":
        "sha256:d0fa47764cc918bff0d567eb6528d7f8708f6c7e7ea143f6034004f8af69e175",
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
    art = worldyard.build_artifact(spec)
    assert art["input_digest"] == V0_INPUT_DIGEST
    assert art["artifact_hash"] == V0_ARTIFACT_HASH
    assert worldyard.verify_artifact(art, spec)


def test_all_vintages_reproduce():
    specs = glob.glob(os.path.join(HERE, "data", "*", "spec.json"))
    assert specs, "no vintages found under data/"
    for spec_p in specs:
        d = os.path.dirname(spec_p)
        spec = _load(spec_p)
        art_disk = _load(os.path.join(d, "artifact.json"))
        art_built = worldyard.build_artifact(spec)
        assert art_built == art_disk, "vintage %s does not reproduce" % d
        assert worldyard.verify_artifact(art_disk, spec), \
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


V0_4 = "v0.4-ppp-unwpp-2026-05-15"


def _v0_4():
    d = os.path.join(HERE, "data", V0_4)
    return _load(os.path.join(d, "spec.json")), _load(os.path.join(d, "artifact.json"))


def _wb_response(spec):
    """The pinned World Bank response, numbers kept as their exact tokens."""
    p = spec["provenance"]["ppp"]
    with open(os.path.join(HERE, p["response_file"]), "rb") as fh:
        raw = fh.read()
    assert hashlib.sha256(raw).hexdigest() == p["response_sha256"]
    assert len(raw) == int(p["response_bytes"])
    head, rows = json.loads(raw.decode("utf-8"), parse_float=str, parse_int=str)
    assert head["lastupdated"] == p["wdi_last_updated"]
    return {r["countryiso3code"]: r for r in rows}


def test_v0_4_populations_and_members_are_v0_3s():
    """v0.4 uses exactly v0.3-unwpp's UN populations and 21-member euro area."""
    spec4, _ = _v0_4()
    spec3, _ = _v0_3()
    assert [(e["code"], e["population"]) for e in spec4["basket"]] == \
        [(e["code"], e["population"]) for e in spec3["basket"]]
    ea4 = dict(spec4["provenance"]["euro_area"])
    assert ea4.pop("same_as") == "v0.3-unwpp-2026-05-15"
    assert ea4 == spec3["provenance"]["euro_area"]
    pop4 = dict(spec4["provenance"]["population"])
    assert pop4.pop("same_as") == "v0.3-unwpp-2026-05-15"
    assert pop4 == spec3["provenance"]["population"]


def test_v0_4_ppp_is_the_pinned_world_bank_response():
    """Every PPP factor is the verbatim token of the pinned response; the
    euro-area factor is the population-weighted blend of the 21 members,
    recomputed here from the response and the UN extract; the valuation leg
    is 1/factor; the World Bank publishes no euro-area value."""
    import make_vintages as mv
    spec, _ = _v0_4()
    wb = _wb_response(spec)
    un = mv.load_un_extract()
    assert wb["EMU"]["value"] is None
    members = spec["provenance"]["euro_area"]["members_iso3"]
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        num = sum(Decimal(un[i]["population_persons"]) * Decimal(wb[i]["value"])
                  for i in members)
        den = sum(Decimal(un[i]["population_persons"]) for i in members)
        blend = num / den
        for e in spec["basket"]:
            if e["code"] == "EUR":
                assert e["ppp_factor_lcu_per_intl_usd"] == str(blend)
            else:
                iso = mv.ISO3_FOR_CCY[e["code"]]
                assert e["ppp_factor_lcu_per_intl_usd"] == wb[iso]["value"]
            assert Decimal(e["fx_valuation_usd_per_unit"]) == \
                Decimal(1) / Decimal(e["ppp_factor_lcu_per_intl_usd"])
    assert "BGR" in members and len(members) == 21


def test_v0_4_ppp_labels_follow_the_world_bank():
    """Labels come from the World Bank's own footnotes: no footnote = an ICP
    2021 extrapolation (China, India); 'Eurostat-OECD annual PPP' = that
    programme's annual PPP; the US is the base. Nothing claims ICP 2024."""
    import make_vintages as mv
    spec, _ = _v0_4()
    wb = _wb_response(spec)
    for e in spec["basket"]:
        assert "ICP 2024" not in e["ppp_basis"]
        if e["code"] == "EUR":
            assert "blend" in e["ppp_basis"] and "Eurostat-OECD" in e["ppp_basis"]
            continue
        iso = mv.ISO3_FOR_CCY[e["code"]]
        if iso == "USA":
            assert e["ppp_basis"].startswith("1 by definition")
        elif wb[iso]["footnote"] == "":
            assert e["ppp_basis"].startswith("ICP 2021 benchmark, extrapolated")
            assert iso in ("CHN", "IND")
        else:
            assert wb[iso]["footnote"] == "Eurostat-OECD annual PPP"
            assert e["ppp_basis"].startswith("Eurostat-OECD")
    for iso in spec["provenance"]["euro_area"]["members_iso3"]:
        assert wb[iso]["footnote"] == "Eurostat-OECD annual PPP", iso
    assert spec["provenance"]["ppp"]["label"].startswith("Not ICP 2024")


def test_v0_4_nominal_fx_is_v0_2s():
    """The baseline leg is the same ECB nominal FX (2026-05-15) as v0.2."""
    spec4, _ = _v0_4()
    spec2 = _load(os.path.join(HERE, "data", "v0.2-ppp-2026-05-15", "spec.json"))
    assert [(e["code"], e["fx_baseline_usd_per_unit"]) for e in spec4["basket"]] \
        == [(e["code"], e["fx_baseline_usd_per_unit"]) for e in spec2["basket"]]


def test_v0_4_supersedes_v0_2():
    spec4, _ = _v0_4()
    art2 = _load(os.path.join(HERE, "data", "v0.2-ppp-2026-05-15", "artifact.json"))
    (sup,) = spec4["supersedes"]
    assert sup["vintage"] == "v0.2-ppp-2026-05-15"
    assert sup["artifact_hash"] == art2["artifact_hash"]
    assert [r["code"] for r in sup["reasons"]] == [
        "EURO_AREA_MEMBERSHIP", "POPULATION_VIA_REPUBLISHER",
        "POPULATION_MISMATCH", "PPP_LABEL", "PPP_REVISED"]


def test_v0_4_input_states_resolve():
    """The recorded input states are what resolve_input returns under the
    declared maximum ages, and none is unavailable."""
    spec, _ = _v0_4()
    st = spec["provenance"]["input_states"]
    for key in ("ecb_fx", "population", "ppp"):
        s = st[key]
        r = worldyard.resolve_input(
            st["target"],
            {"observations": [{"date": s["observation_date"], "value": "1"}]},
            worldyard.DECLARED_MAX_AGE_DAYS[s["source"]])
        assert r["state"] == s["state"] != "unavailable", key
        assert r["age_days"] == s["age_days"] and r["flags"] == s["flags"], key
        assert s["max_age_days"] == str(worldyard.DECLARED_MAX_AGE_DAYS[s["source"]])
    assert st["ecb_fx"]["state"] == "ok"


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
