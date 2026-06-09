#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_vintages.py -- regenerate the pinned data vintages under data/.

It embeds the *raw* source numbers (exactly as published) and derives the
engine inputs with the same exact arithmetic the engine uses, then writes,
for each vintage:
    data/<id>/spec.json       engine input (what gets hashed)
    data/<id>/artifact.json   built + self-verified artifact
    data/<id>/SOURCES.md      provenance: URLs, dates, raw values, conversion

Run from the repository root:
    python3 make_vintages.py            # (re)write the vintages under data/
    python3 make_vintages.py --verify   # recompute in memory and compare to the
                                        # files on disk; nonzero exit on mismatch
Re-running is deterministic: identical bytes, identical hashes.

NOTE on honesty:
  - v0.1 uses REAL data (ECB euro reference rates + UN WPP 2024 population).
  - v0.2 demonstrates the PPP MECHANISM but its PPP factors are ILLUSTRATIVE
    (clearly labelled). The procedure to drop in verified World Bank PA.NUS.PPP
    values is documented in data/<v0.2 id>/SOURCES.md and in SPEC.md section 7.
"""

import os
import json
import argparse
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

import openunit  # the engine (same directory / installed package)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

PREC = 50
ROUND = ROUND_HALF_EVEN


# ---------------------------------------------------------------------------
# RAW SOURCE DATA  (transcribe exactly as published; do not pre-divide)
# ---------------------------------------------------------------------------

# ECB euro foreign exchange reference rates -- units of currency per 1 EUR.
# Source: European Central Bank.
#   daily : https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
#   90-day: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml
ECB = {
    "baseline": {  # reference date 2026-01-09
        "date": "2026-01-09",
        "per_eur": {"USD": "1.1642", "JPY": "183.52", "GBP": "0.8677",
                    "CNY": "8.1288", "INR": "105.0335"},  # EUR itself == 1
    },
    "valuation": {  # reference date 2026-05-15
        "date": "2026-05-15",
        "per_eur": {"USD": "1.1628", "JPY": "184.36", "GBP": "0.87050",
                    "CNY": "7.9194", "INR": "111.5940"},
    },
}

# UN World Population Prospects 2024 Revision (medium variant), 2026 estimate.
# Retrieved 2026-06-08 via Worldometer (which republishes the UN figures).
#   https://www.worldometers.info/world-population/population-by-country/
POP = {
    "IND": "1476625576",   # India
    "CHN": "1412914089",   # China
    "USA": "349035494",    # United States
    "JPN": "122427731",    # Japan
    "GBR": "69931528",     # United Kingdom
}

# Euro area = sum of the 20 member states (same UN/Worldometer source).
EURO_AREA_MEMBERS = [
    ("Germany", "83644258"), ("France", "66746401"), ("Italy", "58926166"),
    ("Spain", "47850793"), ("Netherlands", "18448775"), ("Belgium", "11774642"),
    ("Greece", "9897115"), ("Portugal", "10395362"), ("Austria", "9107266"),
    ("Ireland", "5356950"), ("Croatia", "3822345"), ("Lithuania", "2797338"),
    ("Slovenia", "2114573"), ("Latvia", "1835935"), ("Estonia", "1331062"),
    ("Cyprus", "1382334"), ("Luxembourg", "687448"), ("Malta", "549011"),
    ("Slovakia", "5451342"), ("Finland", "5621739"),
]

# ILLUSTRATIVE PPP conversion factors (LCU per international $), GDP basis.
# *** NOT authoritative -- order-of-magnitude placeholders to exercise v0.2. ***
# Replace with verified World Bank PA.NUS.PPP values (see SOURCES.md procedure).
PPP_ILLUSTRATIVE = {
    "USD": "1.0",      # base currency of the international dollar (exact)
    "EUR": "0.73",     # euro-area approximation (illustrative)
    "CNY": "4.2",      # illustrative
    "JPY": "95.0",     # illustrative
    "GBP": "0.70",     # illustrative
    "INR": "23.5",     # illustrative
}

CCY_NAME = {"USD": "United States", "EUR": "Euro area", "CNY": "China",
            "JPY": "Japan", "GBP": "United Kingdom", "INR": "India"}

# Basket order is fixed and explicit (deliberate, contestable -- see SPEC sec 8):
# the SDR basket, re-weighted by population, plus the most populous economy the
# SDR omits (India).
BASKET = ["USD", "EUR", "CNY", "JPY", "GBP", "INR"]
POP_FOR_CCY = {
    "USD": POP["USA"], "CNY": POP["CHN"], "JPY": POP["JPN"],
    "GBP": POP["GBR"], "INR": POP["IND"],
}  # EUR filled in below from the euro-area sum


def euro_area_total():
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = ROUND
        return sum((Decimal(p) for _, p in EURO_AREA_MEMBERS), Decimal(0))


def usd_per_unit(ccy, leg):
    """Derive USD per 1 unit of `ccy` from ECB EUR-base rates for `leg`."""
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = ROUND
        per_eur = ECB[leg]["per_eur"]
        usd_per_eur = Decimal(per_eur["USD"])
        if ccy == "USD":
            return Decimal(1)
        if ccy == "EUR":
            return usd_per_eur
        return usd_per_eur / Decimal(per_eur[ccy])


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def dump_json(obj):
    # Human-readable on disk; the *hash* always uses openunit.canonical().
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# v0.1  -- REAL: UN population weights, ECB nominal FX (baseline -> valuation)
# ---------------------------------------------------------------------------
def build_v0_1(persist=True):
    ea_pop = euro_area_total()
    pop_for = dict(POP_FOR_CCY)
    pop_for["EUR"] = str(ea_pop)

    basket = []
    for c in BASKET:
        basket.append({
            "code": c,
            "name": CCY_NAME[c],
            "population": pop_for[c],
            "fx_baseline_usd_per_unit": str(usd_per_unit(c, "baseline")),
            "fx_valuation_usd_per_unit": str(usd_per_unit(c, "valuation")),
            # raw ECB rate = currency units per 1 EUR (EUR itself -> "1"):
            "source_eur_per_unit_baseline":
                ECB["baseline"]["per_eur"].get(c, "1"),
            "source_eur_per_unit_valuation":
                ECB["valuation"]["per_eur"].get(c, "1"),
        })

    spec = {
        "method": "openunit",
        "method_version": "v0.1",
        "numeraire": "USD",
        "weight_vintage": {
            "label": "UN-WPP-2024",
            "basis": "population_share",
            "frequency": "low (annual); value uses ECB daily reference FX",
            "note": ("SDR-style fixed basket, population version. Quantities are "
                     "pinned from UN population shares; value is read from ECB "
                     "euro reference rates."),
        },
        "rounding": {"precision": PREC, "mode": "ROUND_HALF_EVEN", "display_dp": 6},
        "provenance": {
            "population": {
                "source": "United Nations, World Population Prospects 2024 "
                           "Revision (medium variant), 2026 estimate",
                "via": "https://www.worldometers.info/world-population/"
                       "population-by-country/",
                "retrieved": "2026-06-08",
                "euro_area_definition": "sum of the 20 euro-area member states",
            },
            "fx": {
                "source": "European Central Bank, euro foreign exchange "
                          "reference rates (units of currency per 1 EUR)",
                "baseline_url": "https://www.ecb.europa.eu/stats/eurofxref/"
                                "eurofxref-hist-90d.xml",
                "valuation_url": "https://www.ecb.europa.eu/stats/eurofxref/"
                                 "eurofxref-daily.xml",
                "baseline_date": ECB["baseline"]["date"],
                "valuation_date": ECB["valuation"]["date"],
                "conversion": "usd_per_unit(C) = (USD per EUR) / (C per EUR); "
                              "USD=1; EUR=(USD per EUR)",
            },
        },
        "basket": basket,
    }
    art = openunit.build_artifact(spec)
    assert openunit.verify_artifact(art, spec), "v0.1 failed self-verification"

    vid = "v0.1-%s" % ECB["valuation"]["date"]
    sources = sources_v0_1(spec, art, ea_pop)
    if persist:
        d = os.path.join(DATA, vid)
        write(os.path.join(d, "spec.json"), dump_json(spec))
        write(os.path.join(d, "artifact.json"), dump_json(art))
        write(os.path.join(d, "SOURCES.md"), sources)
    return vid, spec, art, sources


def sources_v0_1(spec, art, ea_pop):
    lines = []
    lines.append("# openunit vintage `%s` -- sources & provenance\n" % (
        "v0.1-" + ECB["valuation"]["date"]))
    lines.append("**Status: REAL DATA.** Every input below is transcribed from a "
                 "named public source. Re-running `make_vintages.py` reproduces "
                 "`spec.json` and `artifact.json` byte for byte.\n")
    lines.append("- `input_digest`  : `%s`" % art["input_digest"])
    lines.append("- `artifact_hash` : `%s`\n" % art["artifact_hash"])

    lines.append("## Foreign exchange (ECB euro reference rates)\n")
    lines.append("Units of currency per 1 EUR, exactly as published by the "
                 "European Central Bank.\n")
    lines.append("| currency | per EUR @ %s | per EUR @ %s |" % (
        ECB["baseline"]["date"], ECB["valuation"]["date"]))
    lines.append("|---|---|---|")
    lines.append("| EUR | 1 (base) | 1 (base) |")
    for c in ["USD", "JPY", "GBP", "CNY", "INR"]:
        lines.append("| %s | %s | %s |" % (
            c, ECB["baseline"]["per_eur"][c], ECB["valuation"]["per_eur"][c]))
    lines.append("")
    lines.append("- baseline (%s): %s" % (ECB["baseline"]["date"],
                 spec["provenance"]["fx"]["baseline_url"]))
    lines.append("- valuation (%s): %s" % (ECB["valuation"]["date"],
                 spec["provenance"]["fx"]["valuation_url"]))
    lines.append("- conversion to the USD numeraire: "
                 "`usd_per_unit(C) = (USD per EUR) / (C per EUR)`, with `USD=1` "
                 "and `EUR=(USD per EUR)`.\n")

    lines.append("## Population (UN World Population Prospects 2024 Revision)\n")
    lines.append("Medium-fertility variant, 2026 estimate; retrieved 2026-06-08 "
                 "via Worldometer, which republishes the UN figures.\n")
    lines.append("| economy | population |")
    lines.append("|---|---|")
    for c in BASKET:
        e = next(x for x in spec["basket"] if x["code"] == c)
        lines.append("| %s (%s) | %s |" % (CCY_NAME[c], c, e["population"]))
    lines.append("")
    lines.append("### Euro area = sum of 20 member states\n")
    lines.append("| member | population |")
    lines.append("|---|---|")
    for name, p in EURO_AREA_MEMBERS:
        lines.append("| %s | %s |" % (name, p))
    lines.append("| **euro area total** | **%s** |" % ea_pop)
    lines.append("")
    lines.append("Source page: %s\n" % spec["provenance"]["population"]["via"])

    lines.append("## How to verify\n")
    lines.append("```\npython3 make_vintages.py            # regenerate\n"
                 "python3 cli.py verify data/%s/artifact.json data/%s/spec.json\n```\n"
                 % ("v0.1-" + ECB["valuation"]["date"],
                    "v0.1-" + ECB["valuation"]["date"]))
    lines.append("The two ECB URLs above are revised over time; the exact rates "
                 "for the pinned dates are reproduced in the table above so the "
                 "vintage stays verifiable independently of the live feed.\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# v0.2  -- PPP-aware: UN population weights, value read in PPP (international $)
#          (PPP factors are ILLUSTRATIVE -- see note above)
# ---------------------------------------------------------------------------
def build_v0_2(persist=True):
    ea_pop = euro_area_total()
    pop_for = dict(POP_FOR_CCY)
    pop_for["EUR"] = str(ea_pop)

    basket = []
    for c in BASKET:
        # baseline leg : nominal market FX on the valuation date (USD per unit)
        # valuation leg: PPP international-$ per unit = 1 / PPP_factor
        nominal = usd_per_unit(c, "valuation")
        with localcontext() as ctx:
            ctx.prec = PREC
            ctx.rounding = ROUND
            ppp_rate = Decimal(1) / Decimal(PPP_ILLUSTRATIVE[c])
        basket.append({
            "code": c,
            "name": CCY_NAME[c],
            "population": pop_for[c],
            "fx_baseline_usd_per_unit": str(nominal),
            "fx_valuation_usd_per_unit": str(ppp_rate),
            "ppp_factor_lcu_per_intl_usd": PPP_ILLUSTRATIVE[c],
            "ppp_status": "ILLUSTRATIVE_NOT_AUTHORITATIVE",
        })

    spec = {
        "method": "openunit",
        "method_version": "v0.2",
        "numeraire": "USD",
        "weight_vintage": {
            "label": "UN-WPP-2024 + PPP(illustrative)",
            "basis": "population_share",
            "frequency": "low; baseline=nominal FX, valuation=PPP (international $)",
            "note": ("One person, one vote (population weights). The baseline leg "
                     "is nominal market FX; the valuation leg is PPP, so the unit "
                     "is read in international dollars. realized_weight_at_valuation "
                     "shows how real purchasing power redistributes effective "
                     "weight toward lower-price economies."),
        },
        "rounding": {"precision": PREC, "mode": "ROUND_HALF_EVEN", "display_dp": 6},
        "disclaimer": "PPP_FACTORS_ILLUSTRATIVE_NOT_AUTHORITATIVE",
        "provenance": {
            "population": {
                "source": "United Nations, World Population Prospects 2024 "
                           "Revision (medium variant), 2026 estimate",
                "via": "https://www.worldometers.info/world-population/"
                       "population-by-country/",
                "retrieved": "2026-06-08",
            },
            "nominal_fx": {
                "source": "ECB euro reference rates",
                "date": ECB["valuation"]["date"],
                "url": "https://www.ecb.europa.eu/stats/eurofxref/"
                       "eurofxref-daily.xml",
            },
            "ppp": {
                "intended_source": "World Bank, PPP conversion factor, GDP "
                                    "(LCU per international $), indicator "
                                    "PA.NUS.PPP",
                "url": "https://data.worldbank.org/indicator/PA.NUS.PPP",
                "status": "ILLUSTRATIVE placeholders; replace with verified "
                          "World Bank values before any non-demonstration use",
            },
        },
        "basket": basket,
    }
    art = openunit.build_artifact(spec)
    assert openunit.verify_artifact(art, spec), "v0.2 failed self-verification"

    vid = "v0.2-ppp-illustrative-%s" % ECB["valuation"]["date"]
    sources = sources_v0_2(spec, art)
    if persist:
        d = os.path.join(DATA, vid)
        write(os.path.join(d, "spec.json"), dump_json(spec))
        write(os.path.join(d, "artifact.json"), dump_json(art))
        write(os.path.join(d, "SOURCES.md"), sources)
    return vid, spec, art, sources


def sources_v0_2(spec, art):
    lines = []
    lines.append("# openunit vintage `%s` -- sources & provenance\n" % (
        "v0.2-ppp-illustrative-" + ECB["valuation"]["date"]))
    lines.append("**Status: MECHANISM REAL, PPP DATA ILLUSTRATIVE.**\n")
    lines.append("Population (UN WPP 2024) and the nominal-FX baseline (ECB) are "
                 "real. The **PPP factors are placeholders** chosen only to "
                 "exercise the v0.2 mechanism end to end. They are **not** World "
                 "Bank values and must not be used as an authoritative figure.\n")
    lines.append("- `input_digest`  : `%s`" % art["input_digest"])
    lines.append("- `artifact_hash` : `%s`\n" % art["artifact_hash"])

    lines.append("## PPP factors used (ILLUSTRATIVE)\n")
    lines.append("PPP conversion factor = local-currency units per international $; "
                 "PPP rate = `1 / factor` (international $ per unit), used as the "
                 "valuation leg.\n")
    lines.append("| currency | PPP factor (illustrative) | status |")
    lines.append("|---|---|---|")
    for c in BASKET:
        lines.append("| %s | %s | ILLUSTRATIVE |" % (c, PPP_ILLUSTRATIVE[c]))
    lines.append("")

    lines.append("## Procedure to make this vintage REAL\n")
    lines.append("1. Open the World Bank series PA.NUS.PPP "
                 "(PPP conversion factor, GDP, LCU per international $): "
                 "<https://data.worldbank.org/indicator/PA.NUS.PPP>.")
    lines.append("2. For each currency, read the most recent year's value "
                 "(US = 1.0 by definition). For the euro area, choose and "
                 "document an aggregation rule (e.g. a GDP-weighted blend of "
                 "member states, or Eurostat's euro-area price level), because "
                 "the World Bank does not publish a single euro-area PPP factor.")
    lines.append("3. Replace the entries in `PPP_ILLUSTRATIVE` in "
                 "`make_vintages.py`, set `ppp_status` to the source/year, and "
                 "re-run `python3 make_vintages.py`.")
    lines.append("4. The new `spec.json` / `artifact.json` hashes will change "
                 "(new inputs) and the vintage id should be renamed to drop "
                 "`illustrative`.\n")
    lines.append("Why the euro area needs a rule: the euro area spans countries "
                 "with materially different price levels, so there is no unique "
                 "'euro-area PPP'. openunit's stance is to make that choice "
                 "explicit rather than hide it (see SPEC.md section 8).\n")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="make_vintages.py",
        description="Regenerate or verify the pinned openunit data vintages.")
    ap.add_argument(
        "--verify", action="store_true",
        help="recompute every vintage in memory and compare it to the files "
             "under data/ WITHOUT writing; exit nonzero on any mismatch")
    args = ap.parse_args(argv)

    built = [build_v0_1(persist=not args.verify),
             build_v0_2(persist=not args.verify)]

    if not args.verify:
        for vid, _spec, art, _src in built:
            print("wrote data/%s   value=%s   hash=%s"
                  % (vid, art["value_usd"][:8], art["artifact_hash"]))
        return 0

    failed = 0
    for vid, spec, art, sources in built:
        d = os.path.join(DATA, vid)
        problems = []
        for name, regen in (("spec.json", dump_json(spec)),
                            ("artifact.json", dump_json(art)),
                            ("SOURCES.md", sources)):
            p = os.path.join(d, name)
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    on_disk = fh.read()
            except FileNotFoundError:
                problems.append("%s missing" % name)
                continue
            if on_disk != regen:
                problems.append("%s differs from regenerated output" % name)
        if not openunit.verify_artifact(art, spec):
            problems.append("verify_artifact returned False")
        if problems:
            failed += 1
            print("FAIL  %s: %s" % (vid, "; ".join(problems)))
        else:
            print("PASS  %s reproduces  hash=%s" % (vid, art["artifact_hash"]))
    print("-" * 50)
    print("%d/%d vintages reproduce" % (len(built) - failed, len(built)))
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
