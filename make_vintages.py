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
  - v0.2 uses REAL data too: World Bank PA.NUS.PPP (ICP, year PPP_YEAR) for
    USD/CNY/JPY/GBP/INR. The World Bank publishes no single Euro-area PA.NUS.PPP
    value, so the euro-area factor is a population-weighted blend of the 20
    euro-area members' WB values -- a contestable choice (SPEC.md section 10)
    documented in the vintage's SOURCES.md.
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

# PPP reference year (World Bank PA.NUS.PPP / ICP round).
PPP_YEAR = "2024"

# World Bank PA.NUS.PPP -- PPP conversion factor, GDP (LCU per international $),
# ICP, reference year 2024 -- transcribed exactly as published (full digits).
#   https://data.worldbank.org/indicator/PA.NUS.PPP   (CC BY-4.0)
# EUR is filled in below from euro_area_ppp(): the World Bank publishes NO single
# Euro-area PA.NUS.PPP value, so the euro-area factor is a population-weighted
# blend of the 20 euro-area members' WB values (see euro_area_ppp / SOURCES.md).
PPP_WB = {
    "USD": "1.0",                 # international-dollar base (exact, = 1)
    "CNY": "3.5325492491585",     # China
    "JPY": "94.462599",           # Japan
    "GBP": "0.664153",            # United Kingdom
    "INR": "20.4219876045922",    # India
    # "EUR": filled below = population-weighted blend of euro-area members
}

# Per-member World Bank PA.NUS.PPP (year 2024, EUR per international $),
# transcribed exactly as published. Member populations come from
# EURO_AREA_MEMBERS above (UN WPP 2024) -- the same basis as the v0.1 euro-area
# headcount -- so the blend uses one consistent population source.
EURO_PPP_2024 = {
    "Germany": "0.700862", "France": "0.681239", "Italy": "0.599627",
    "Spain": "0.562107", "Netherlands": "0.731421", "Belgium": "0.704288",
    "Greece": "0.515086", "Portugal": "0.515993", "Austria": "0.710451",
    "Ireland": "0.740894", "Croatia": "0.44841971235566",
    "Lithuania": "0.49104", "Slovenia": "0.550461", "Latvia": "0.496528",
    "Estonia": "0.576166", "Cyprus": "0.56709589608174",
    "Luxembourg": "0.815579", "Malta": "0.580522225637102",
    "Slovakia": "0.501903", "Finland": "0.753945",
}

# World Bank nominal GDP, NY.GDP.MKTP.CD (current US$), year 2024 -- transcribed
# exactly as published. Used ONLY to document a GDP-weighted *sensitivity* for
# the euro-area PPP blend (SPEC sec 10 / the sensitivity table in v0.2
# SOURCES.md). The SHIPPED euro-area factor stays population-weighted; these
# values feed no spec, no artifact, and change no hash.
#   https://data.worldbank.org/indicator/NY.GDP.MKTP.CD   (CC BY-4.0)
#   retrieved 2026-06-10; World Bank "last updated" 2026-04-08.
EURO_GDP_2024 = {
    "Germany": "4685592577804.69", "France": "3160442622465.08",
    "Italy": "2380825077243.59", "Spain": "1725671652742.19",
    "Netherlands": "1214927698572.66", "Belgium": "671370081636.406",
    "Greece": "256238371778.118", "Portugal": "313271185085.102",
    "Austria": "534790720466.822", "Ireland": "609157459747.205",
    "Croatia": "92983810328.9088", "Lithuania": "84869215513.3648",
    "Slovenia": "72972015197.3859", "Latvia": "43684254432.3609",
    "Estonia": "43130419829.35", "Cyprus": "37634533331.8902",
    "Luxembourg": "93279851863.4062", "Malta": "24971574502.4475",
    "Slovakia": "140934076532.375", "Finland": "298696961297.656",
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


def euro_area_ppp():
    """Euro-area PA.NUS.PPP as a population-weighted blend of the 20 member
    states:  Sum(pop_i * ppp_i) / Sum(pop_i).

    The World Bank publishes no single Euro-area PA.NUS.PPP value, so we blend
    the members' published values weighted by UN WPP 2024 population. Weighting
    by people (rather than GDP) follows openunit's one-person-one-vote stance and
    is a contestable choice, documented as such (SPEC sec 10 / SOURCES.md).
    """
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = ROUND
        num = sum((Decimal(p) * Decimal(EURO_PPP_2024[name])
                   for name, p in EURO_AREA_MEMBERS), Decimal(0))
        den = sum((Decimal(p) for _, p in EURO_AREA_MEMBERS), Decimal(0))
        return num / den


def euro_area_ppp_gdp_weighted():
    """GDP-weighted euro-area PA.NUS.PPP, for the SENSITIVITY note only:
    Sum(gdp_i * ppp_i) / Sum(gdp_i), with member nominal GDP from World Bank
    NY.GDP.MKTP.CD (2024). This is NOT the shipped factor (the shipped one is
    the population-weighted blend in euro_area_ppp); it exists so SOURCES.md can
    state, on the record, what a GDP weighting would yield (SPEC sec 10).
    """
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = ROUND
        num = sum((Decimal(EURO_GDP_2024[name]) * Decimal(EURO_PPP_2024[name])
                   for name, _ in EURO_AREA_MEMBERS), Decimal(0))
        den = sum((Decimal(EURO_GDP_2024[name])
                   for name, _ in EURO_AREA_MEMBERS), Decimal(0))
        return num / den


def v0_2_value_for_euro_ppp(euro_ppp):
    """1 openunit in international $ (v0.2) if the euro-area PPP factor were
    `euro_ppp`. Used only to report the GDP-weighted sensitivity; the value
    depends solely on the basket numbers, so provenance fields are omitted.
    Passing euro_area_ppp() reproduces the shipped v0.2 value exactly.
    """
    pop_for = dict(POP_FOR_CCY)
    pop_for["EUR"] = str(euro_area_total())
    ppp = dict(PPP_WB)
    ppp["EUR"] = str(euro_ppp)
    basket = []
    for c in BASKET:
        nominal = usd_per_unit(c, "valuation")
        with localcontext() as ctx:
            ctx.prec = PREC
            ctx.rounding = ROUND
            ppp_rate = Decimal(1) / Decimal(ppp[c])
        basket.append({
            "code": c, "name": CCY_NAME[c], "population": pop_for[c],
            "fx_baseline_usd_per_unit": str(nominal),
            "fx_valuation_usd_per_unit": str(ppp_rate),
        })
    spec = {
        "method": "openunit", "method_version": "v0.2", "numeraire": "USD",
        "weight_vintage": {"label": "sensitivity", "basis": "population_share"},
        "rounding": {"precision": PREC, "mode": "ROUND_HALF_EVEN", "display_dp": 6},
        "basket": basket,
    }
    return Decimal(openunit.build_artifact(spec)["value_usd"])


# Fill EUR from the population-weighted member blend (full precision; the member
# table and formula in SOURCES.md let anyone recompute this exact value).
PPP_WB["EUR"] = str(euro_area_ppp())


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
#          (REAL World Bank PA.NUS.PPP; euro area = population-weighted member
#           blend -- see PPP_WB / euro_area_ppp above)
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
            ppp_rate = Decimal(1) / Decimal(PPP_WB[c])
        basket.append({
            "code": c,
            "name": CCY_NAME[c],
            "population": pop_for[c],
            "fx_baseline_usd_per_unit": str(nominal),
            "fx_valuation_usd_per_unit": str(ppp_rate),
            "ppp_factor_lcu_per_intl_usd": PPP_WB[c],
            "ppp_status": "World Bank PA.NUS.PPP (ICP) " + PPP_YEAR,
        })

    spec = {
        "method": "openunit",
        "method_version": "v0.2",
        "numeraire": "USD",
        "weight_vintage": {
            "label": "UN-WPP-2024 + WB-PPP-" + PPP_YEAR,
            "basis": "population_share",
            "frequency": "low; baseline=nominal FX, valuation=PPP (international $)",
            "note": ("One person, one vote (population weights). The baseline leg "
                     "is nominal market FX; the valuation leg is PPP, so the unit "
                     "is read in international dollars. realized_weight_at_valuation "
                     "shows how real purchasing power redistributes effective "
                     "weight toward lower-price economies."),
        },
        "rounding": {"precision": PREC, "mode": "ROUND_HALF_EVEN", "display_dp": 6},
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
                "source": "World Bank, PPP conversion factor, GDP "
                          "(LCU per international $), indicator PA.NUS.PPP (ICP)",
                "url": "https://data.worldbank.org/indicator/PA.NUS.PPP",
                "year": PPP_YEAR,
                "license": "CC BY-4.0",
                "euro_area_method": (
                    "The World Bank publishes no single Euro-area PA.NUS.PPP "
                    "value, so the euro-area factor is a population-weighted "
                    "blend of the 20 member states' WB PA.NUS.PPP: "
                    "sum(pop_i * ppp_i) / sum(pop_i), with member populations "
                    "from UN WPP 2024 (same basis as the euro-area headcount). "
                    "Weighting by people rather than GDP follows openunit's "
                    "one-person-one-vote stance and is a contestable choice "
                    "(SPEC sec 10)."),
            },
        },
        "basket": basket,
    }
    art = openunit.build_artifact(spec)
    assert openunit.verify_artifact(art, spec), "v0.2 failed self-verification"

    vid = "v0.2-ppp-%s" % ECB["valuation"]["date"]
    sources = sources_v0_2(spec, art)
    if persist:
        d = os.path.join(DATA, vid)
        write(os.path.join(d, "spec.json"), dump_json(spec))
        write(os.path.join(d, "artifact.json"), dump_json(art))
        write(os.path.join(d, "SOURCES.md"), sources)
    return vid, spec, art, sources


def sources_v0_2(spec, art):
    euro = euro_area_ppp()
    ea_pop = euro_area_total()
    lines = []
    lines.append("# openunit vintage `%s` -- sources & provenance\n" % (
        "v0.2-ppp-" + ECB["valuation"]["date"]))
    lines.append("**Status: REAL DATA.** Population (UN WPP 2024), the nominal-FX "
                 "baseline (ECB), and the PPP valuation leg (World Bank "
                 "`PA.NUS.PPP`, ICP %s) are all transcribed from named public "
                 "sources. Re-running `make_vintages.py` reproduces `spec.json` "
                 "and `artifact.json` byte for byte.\n" % PPP_YEAR)
    lines.append("- `input_digest`  : `%s`" % art["input_digest"])
    lines.append("- `artifact_hash` : `%s`\n" % art["artifact_hash"])

    lines.append("## PPP conversion factors (World Bank `PA.NUS.PPP`, ICP %s)\n"
                 % PPP_YEAR)
    lines.append("PPP conversion factor = local-currency units per international $ "
                 "(GDP basis); the valuation leg is `PPP rate = 1 / factor` "
                 "(international $ per unit). Values are transcribed exactly as "
                 "published.\n")
    lines.append("- source: World Bank, *PPP conversion factor, GDP "
                 "(LCU per international $)*, indicator `PA.NUS.PPP` (ICP)")
    lines.append("- url: <https://data.worldbank.org/indicator/PA.NUS.PPP>")
    lines.append("- reference year: **%s**  |  license: **CC BY-4.0**\n" % PPP_YEAR)
    lines.append("| currency | economy | PA.NUS.PPP (%s) |" % PPP_YEAR)
    lines.append("|---|---|---|")
    for c in BASKET:
        if c == "EUR":
            lines.append("| EUR | Euro area | %s *(population-weighted member "
                         "blend, see below)* |" % PPP_WB["EUR"])
        else:
            lines.append("| %s | %s | %s |" % (c, CCY_NAME[c], PPP_WB[c]))
    lines.append("")
    lines.append("(USD = 1.0 is the international-dollar base by definition.)\n")

    lines.append("## Euro area: population-weighted member blend\n")
    lines.append("The World Bank publishes **no single Euro-area `PA.NUS.PPP` "
                 "value** (the `EMU` aggregate row is empty in both the bulk CSV "
                 "and the API). openunit therefore derives the euro-area factor as "
                 "a **population-weighted blend** of the 20 euro-area members:\n")
    lines.append("```\n"
                 "ppp(euro area) = sum(pop_i * ppp_i) / sum(pop_i)\n"
                 "```\n")
    lines.append("Member populations are the UN WPP 2024 figures used for the "
                 "euro-area headcount (one consistent population source); each "
                 "member's `PA.NUS.PPP` is the World Bank %s value.\n" % PPP_YEAR)
    lines.append("| member | population (UN WPP 2024) | PA.NUS.PPP (%s) |"
                 % PPP_YEAR)
    lines.append("|---|---|---|")
    for name, p in EURO_AREA_MEMBERS:
        lines.append("| %s | %s | %s |" % (name, p, EURO_PPP_2024[name]))
    lines.append("| **euro area (blend)** | **%s** | **%s** |" % (ea_pop, euro))
    lines.append("")
    lines.append("Weighting the blend by **people** (rather than by GDP) follows "
                 "openunit's one-person-one-vote stance. It is deliberately a "
                 "**value choice, not a neutral fact**, and is therefore a "
                 "**contestable** input -- exactly the kind of choice openunit "
                 "makes explicit and auditable rather than hiding (see SPEC.md "
                 "section 10). A GDP-weighted blend would yield a different "
                 "euro-area factor; the population-weighted figure is the one "
                 "pinned here, on the record.\n")

    q6 = Decimal("0.000001")
    euro_gdp = euro_area_ppp_gdp_weighted()
    val_pop = v0_2_value_for_euro_ppp(euro)
    val_gdp = v0_2_value_for_euro_ppp(euro_gdp)
    lines.append("## Sensitivity: GDP-weighted euro-area blend (not shipped)\n")
    lines.append("The euro-area weighting is a **contestable value choice** "
                 "(SPEC.md section 10). To make that explicit on the record, here "
                 "is the GDP-weighted alternative computed from the same member "
                 "`PA.NUS.PPP` values, weighted by World Bank nominal GDP "
                 "(`NY.GDP.MKTP.CD`, current US$, 2024) instead of by population:\n")
    lines.append("```\n"
                 "ppp(euro area, GDP-weighted) = sum(gdp_i * ppp_i) / sum(gdp_i)\n"
                 "```\n")
    lines.append("- GDP source: World Bank, *GDP (current US$)*, indicator "
                 "`NY.GDP.MKTP.CD` -- <https://data.worldbank.org/indicator/"
                 "NY.GDP.MKTP.CD> (CC BY-4.0), year **%s**, retrieved 2026-06-10."
                 % PPP_YEAR)
    lines.append("")
    lines.append("| euro-area PPP factor | value | 1 openunit (v0.2) |")
    lines.append("|---|---|---|")
    lines.append("| **population-weighted (shipped)** | %s | **%s international $** |"
                 % (euro.quantize(q6), val_pop.quantize(q6)))
    lines.append("| GDP-weighted (sensitivity only) | %s | %s international $ |"
                 % (euro_gdp.quantize(q6), val_gdp.quantize(q6)))
    lines.append("")
    lines.append("Full-precision GDP-weighted factor: `%s`.\n" % euro_gdp)
    lines.append("Per-member nominal GDP used for the GDP-weighted blend "
                 "(transcribed exactly as published):\n")
    lines.append("| member | nominal GDP 2024 (current US$) | PA.NUS.PPP (%s) |"
                 % PPP_YEAR)
    lines.append("|---|---|---|")
    for name, _ in EURO_AREA_MEMBERS:
        lines.append("| %s | %s | %s |"
                     % (name, EURO_GDP_2024[name], EURO_PPP_2024[name]))
    lines.append("")
    lines.append("**openunit ships the population-weighted factor**, consistent "
                 "with its one-person-one-vote stance (SPEC.md section 10). The "
                 "GDP-weighted figures above change no shipped spec, artifact, or "
                 "hash; they are recorded so a GDP weighting can be argued against "
                 "the exact numbers rather than in the abstract. Here the GDP "
                 "weighting raises the euro-area PPP factor by about 2.8%%, which "
                 "moves 1 openunit by about 0.12%% (%s -> %s international $) -- a "
                 "small but real difference, made in the open.\n"
                 % (val_pop.quantize(q6), val_gdp.quantize(q6)))

    lines.append("## How to verify\n")
    lines.append("```\npython3 make_vintages.py            # regenerate\n"
                 "python3 cli.py verify data/%s/artifact.json data/%s/spec.json\n```\n"
                 % ("v0.2-ppp-" + ECB["valuation"]["date"],
                    "v0.2-ppp-" + ECB["valuation"]["date"]))

    lines.append("## Updating to a future ICP / PPP year\n")
    lines.append("1. Open `PA.NUS.PPP` "
                 "(<https://data.worldbank.org/indicator/PA.NUS.PPP>) and pick the "
                 "latest year `Y` for which USD/CNY/JPY/GBP/INR and the 20 "
                 "euro-area members all have values.")
    lines.append("2. In `make_vintages.py`, set `PPP_YEAR = \"Y\"` and update the "
                 "transcribed values in `PPP_WB` (USD = `\"1.0\"`) and "
                 "`EURO_PPP_2024` (full digits as published).")
    lines.append("3. Re-run `python3 make_vintages.py`. The euro-area factor is "
                 "recomputed from the member blend automatically; the new "
                 "`spec.json` / `artifact.json` hashes change (new inputs).")
    lines.append("4. Update the pinned hashes referenced in `README.md`, "
                 "`ARTIFACT_FORMAT.md`, and `CHANGELOG.md`.\n")
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
