# Worldyard (formerly openunit)

A deterministic, publicly verifiable, **population-weighted unit of account**.

> **Renamed.** This project was called **openunit** up to version 0.3.0. The
> Python module, the command and the method name are now `worldyard`.
> `import openunit` and the `openunit` command still work, with a deprecation
> notice. Vintages built before the rename keep the method name `openunit`
> and every hash they had. The GitHub repository was renamed to `worldyard` on
> 2026-10-26; links to the old name redirect.

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Dependencies](https://img.shields.io/badge/dependencies-none%20(stdlib)-success.svg)

Worldyard is a *measuring stick*, not money. It does not issue a currency, hold
reserves, or settle payments. It defines one thing precisely: a unit of value
whose basket weights count **people**, rather than being set by the issuer of
any single national currency — and it does so reproducibly, so anyone can
recompute the exact same number and the exact same hashes, byte for byte.

> **Don't trust me. Verify me.**

## What it is (and what it is not)

- **It is** a fixed-basket index — the *population version of the SDR method*.
  At a low-frequency "vintage" it pins a fixed *quantity* of each currency,
  derived from population shares; the unit's value is then read from market (or
  PPP) exchange rates.
- **It is not** a token, stablecoin, settlement rail, payment system, or
  investment product. It makes no return prediction and gives no financial
  advice. The reference value is quoted in a numeraire (USD here) only as a
  readable denomination; the *unit itself* is defined by the basket.

## Scope, licence and terms

- **Information only.** Worldyard publishes a reproducible measurement for
  information. It is not offered as a benchmark for financial instruments or
  contracts, nor as the backing or reference value of a token.
- **The licence is not a use restriction, and not an assurance of
  suitability.** The Apache License 2.0 covers the code: it lets anyone use, modify and
  redistribute it, and it does not itself restrict *what* anyone uses Worldyard
  for. Equally, nothing in the licence or in this README says a given use is
  suitable or lawful. Whether a use is regulated (for example as a benchmark)
  depends on how and by whom Worldyard is used, not on this statement; anyone
  who builds on it must check the rules that apply to them.
- **Data terms are separate from the code licence.** Each input keeps its
  publisher's terms (each vintage's `SOURCES.md` names its publishers): the ECB's euro
  reference rates are published "for information purposes only"
  (<https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>)
  and are reused under the ECB's conditions (cite the ECB, state any
  modification; <https://www.ecb.europa.eu/home/disclaimer/html/index.en.html>);
  UN World Population Prospects data are licensed CC BY 3.0 IGO; World Bank
  `PA.NUS.PPP` data CC BY 4.0.
- **Independent.** Worldyard is not affiliated with, endorsed by, or certified
  by IOSCO, the IMF, the ECB, the United Nations, the World Bank, or any other
  authority or standard-setter. Mentions of the SDR method or of these
  publishers describe the method and the inputs only. Any future description of
  Worldyard's governance against published principles (such as IOSCO's
  Principles for Financial Benchmarks) would be a voluntary self-description,
  not a certification.

## Why

Expressing value in a single national currency bakes in the politics of who
issues it. Worldyard counts people equally instead: one person, one vote (a
weighting rule, not a governance mechanism). That is deliberately a **value
choice, not a neutral fact** (see *On "fairness"* below and `SPEC.md` §10) —
the point is to make the choice explicit, fixed, and auditable so it can be
argued in the open rather than hidden inside an opaque index.

## Quickstart

```sh
git clone <repo-url> worldyard && cd worldyard
python3 test_determinism_guard.py     # 4/4 determinism checks
python3 make_vintages.py --verify     # real vintages reproduce, byte for byte
python3 worldyard.py                   # illustrative demo
```

No third-party dependencies — Python **3.10+** (as declared in
`pyproject.toml`), standard library only.

## The reference vintages

Four pinned vintages ship under `data/`. Each has a `spec.json` (the hashed
input), an `artifact.json` (the built, self-verifying result), and a
`SOURCES.md` (full provenance: URLs, dates, raw numbers, and the exact
conversion used). `data/vintages.json` records which vintage supersedes which,
with machine-readable warnings; published vintage files are never rewritten.
Vintages built before the rename (v0.1 to v0.3) carry the method name
`openunit` and quote their value as "1 openunit"; v0.4 carries `worldyard`.
It is the same unit.

### `v0.1-2026-05-15` — **REAL DATA**

Method v0.1 (one person, one vote) on real, named inputs.

- inputs: UN **World Population Prospects 2024** (2026 medium-variant
  projection) + **ECB euro reference rates** (baseline `2026-01-09`, valuation
  `2026-05-15`)
- **provenance note:** the UN figures were transcribed from **Worldometer's
  republication**, not from the UN Population Division's own file; 23 of the
  25 populations equal the UN file and Greece and Slovenia differ by one person
  each. The euro area is counted as **20** members, but Bulgaria had joined on
  2026-01-01. **Superseded by `v0.3-unwpp-2026-05-15`**, which reads the UN
  primary file; this vintage is kept unchanged and still verifies (see
  `data/vintages.json`).
- **1 openunit = 0.985631 USD**
- `artifact_hash` `sha256:1e615cf7…9a3a`
- population-pinned weights: India 39.08 %, China 37.39 %, United States
  9.24 %, euro area 9.20 %, Japan 3.24 %, United Kingdom 1.85 %

### `v0.2-ppp-2026-05-15` — **REAL DATA (World Bank `PA.NUS.PPP`, reference year 2024)**

Method v0.2 (population weights, PPP valuation leg) on real, named inputs: UN
**World Population Prospects 2024** + an **ECB** nominal-FX baseline + **World
Bank `PA.NUS.PPP`** for 2024 on the valuation leg, so the unit is read in
**international dollars**.

- **label correction:** the vintage calls these values "ICP 2024". No ICP
  2024 results have been released (the latest ICP cycle is 2021). In the World
  Bank's WDI the 2024 values are the ICP 2021 benchmark extrapolated to 2024
  (China, India) and Eurostat-OECD annual PPPs (Japan, United Kingdom,
  euro-area members). v0.2 matches WDI's April 2026 release; the World Bank
  has since revised five of its 25 values (`docs/AUDIT.md`,
  `data/vintages.json`).

- provenance note: as in v0.1, populations come from Worldometer's
  republication of UN WPP 2024 and the euro area has 20 members (Bulgaria
  missing); `data/vintages.json` carries these warnings. **Superseded by
  `v0.4-ppp-unwpp-2026-05-15`**; this vintage is kept unchanged and still
  verifies.
- PA.NUS.PPP 2024 for USD/CNY/JPY/GBP/INR, transcribed exactly as published. The
  World Bank publishes **no single Euro-area** `PA.NUS.PPP` value, so the
  euro-area factor is a **population-weighted blend** of the 20 members' WB
  values — a contestable, one-person-one-vote choice (see `SPEC.md` §10 and the
  vintage's `SOURCES.md`), not a World Bank aggregate.
- **1 openunit = 2.848010 international dollars**
- `artifact_hash` `sha256:566c95c1…b97a`
- reading the unit in international dollars shifts *realized* weight toward
  lower-price economies: India moves from a 39.08 % headcount share to a
  64.48 % realized weight at PPP, while the United States falls from 9.24 % to
  3.24 %.

### `v0.3-unwpp-2026-05-15` — **REAL DATA (UN primary file)** — supersedes v0.1

Method v0.1's formulas (method version `v0.3`, under the v0.3 input domain)
and **exactly v0.1's ECB FX inputs**, with populations read from the UN
Population Division's own *World Population Prospects 2024* file (medium
variant, 1 July 2026) instead of a republication, and the euro area counted on its membership at the valuation
date: **21 states** (Bulgaria joined on 2026-01-01). The 26 UN rows used are
committed as `data/sources/un_wpp2024_population_2026.csv` (CC BY 3.0 IGO).

- **1 openunit = 0.985654 USD** (v0.1: 0.985631; +0.0024 %, almost all of it
  from adding Bulgaria)
- `artifact_hash` `sha256:0fe13c83…b7af`
- population-pinned weights: India 39.01 %, China 37.33 %, euro area 9.36 %,
  United States 9.22 %, Japan 3.23 %, United Kingdom 1.85 %

### `v0.4-ppp-unwpp-2026-05-15` — **REAL DATA (PPP, UN primary file)** — supersedes v0.2

Method v0.2's PPP valuation leg (method version `v0.4`; read in
**international dollars**) with v0.3-unwpp's populations (UN Population
Division's own WPP 2024 file, euro area of **21** members) and World Bank
`PA.NUS.PPP` for reference year 2024, taken from one small API response
committed verbatim as `data/sources/wb_pa_nus_ppp_2024_wdi-2026-10-08.json`
(CC BY 4.0, pinned by sha256). The nominal-FX baseline is the same ECB data as v0.2.

- **labelled as the World Bank labels it:** China and India are the ICP 2021
  benchmark extrapolated to 2024 by the World Bank; Japan, the United Kingdom
  and the 21 euro-area members are Eurostat-OECD annual PPPs; US = 1. They are
  not ICP 2024 values (none have been released) and may be revised again
  (`data/vintages.json` warning `PPP_EXTRAPOLATED`).
- the euro-area factor is again a population-weighted blend of the members
  (the World Bank publishes no euro-area value): 0.638144 (v0.2: 0.642950)
- **1 worldyard = 2.845044 international dollars** (v0.2: 2.848010; −0.104 %:
  −0.044 % from the World Bank's July 2026 revisions, the rest from adding
  Bulgaria; the switch to the UN file is negligible)
- `artifact_hash` `sha256:d0fa4776…e175` (method name `worldyard`)
- realized weight at PPP: India 64.34 %, China 25.35 %, euro area 4.43 %,
  United States 3.24 %, Japan 1.91 %, United Kingdom 0.73 % (population
  shares as in v0.3)

## Command-line interface

```sh
worldyard build  spec.json -o artifact.json    # build + self-verify
worldyard verify artifact.json spec.json        # exit 0 iff it reproduces
worldyard show   artifact.json                  # one-screen summary
worldyard anchor artifact.json -o anchor.json [--prev prev.json] [--label L]
worldyard verify-anchor anchor.json artifact.json [--prev prev.json]
```

After a local install (`pip install -e .`) the `worldyard` command is available
(the old `openunit` command still works and prints a deprecation notice);
otherwise run the same subcommands with `python3 cli.py …`. If the old
distribution is installed, run `pip uninstall openunit` before
`pip install -e .`.

In PPP vintages (v0.2, v0.4) the artifact's `numeraire` field stays `USD`; the
value is in international dollars (PPP-adjusted US dollars), as the vintage's
`weight_vintage` and `SOURCES.md` state. `show`, `build` and the demo therefore
print such a value as "international $ (numeraire field: USD)"; this is display
only and changes no hash (`SPEC.md` §2.3).

## Verifying someone else's published value

You need exactly two files: the `spec.json` that was hashed and the
`artifact.json` that was published.

```sh
worldyard verify artifact.json spec.json
```

`verify` returns success only if **all three** hold: the artifact's
`input_digest` matches the spec, the artifact's `artifact_hash` matches its own
content, and rebuilding from the spec reproduces the artifact exactly. Any
single-field edit to either file breaks verification. See `SPEC.md` §5.

## Independent verification (don't even trust the engine)

`worldyard verify` uses the engine to check the engine's own output. If you do
not want to extend even that much trust, `verify_independent.py` is a **second
implementation** of the entire verification procedure, written from `SPEC.md`
and `ARTIFACT_FORMAT.md` alone: it never imports `worldyard`/`openunit`/`cli`/`anchor` and
shares no code with them. It re-derives every weight, amount, value, and both
hashes from the spec, then compares the published artifact field by field
(standard library only):

```sh
python3 verify_independent.py data/v0.1-2026-05-15/spec.json \
                              data/v0.1-2026-05-15/artifact.json
# INDEPENDENT VERIFICATION: PASS
#   input_digest  : sha256:90b54dc5…fe25
#   artifact_hash : sha256:1e615cf7…9a3a
```

Exit 0 means two independent implementations of the published format agree,
byte for byte; any mismatch lists the differing fields and exits 1. Run it over
every shipped vintage with `make verify-independent` (also part of
`make verify` and CI). If the engine were ever wrong or tampered with, this is
the program that would say so.

## Determinism properties

- **Standard library only** (`json`, `hashlib`, `decimal`).
- **Exact arithmetic** with `decimal.Decimal`, precision **50**, rounding
  **ROUND_HALF_EVEN**, inside an isolated `localcontext` (the caller's global
  decimal context is never modified). All numeric inputs are parsed from
  **strings**, never from floats.
- **No wall clock.** The engine never imports or calls `datetime`/`time`; the
  result depends only on the inputs, never on when it runs. (`test_determinism_guard.py`
  enforces this by source scan *and* by poisoning `time.*` at runtime.)
- **Canonical JSON** for every hash: `sort_keys=True`, `separators=(",", ":")`,
  `ensure_ascii=False`, encoded UTF-8.
- **SHA-256**, prefixed `sha256:`, for both `input_digest` and `artifact_hash`.

## Anchoring (tamper-evidence)

Worldyard's value is reproducibility, not authority. The optional anchoring
helper commits an `artifact_hash` to a small, offline, append-only hash-chain
record so a publisher can say "this exact artifact existed by this point and has
not been silently revised." Producing a public, independently-checkable
timestamp (an OpenTimestamps `.ots` proof or a blockchain txid) is an *external*
step and is carried in a field that is **not** part of the commitment, so it can
be attached later without changing any hash. See `docs/ANCHORING.md`.

## Project layout

```
worldyard.py                engine: build_artifact / verify_artifact / resolve_input (+ demo)
openunit.py                 deprecated alias: `import openunit` returns the worldyard module
cli.py                      command-line interface
anchor.py                   tamper-evident anchoring (offline hash-chain)
make_vintages.py            regenerate / --verify the pinned data vintages
verify_independent.py       independent second-implementation verifier (no engine import)
sample_input.json           illustrative v0 spec (non-authoritative)
data/
  v0.1-2026-05-15/          REAL vintage: spec.json, artifact.json, SOURCES.md
  v0.2-ppp-2026-05-15/      REAL PPP vintage: World Bank PA.NUS.PPP 2024
  v0.3-unwpp-2026-05-15/    REAL vintage: UN primary population file; supersedes v0.1
  v0.4-ppp-unwpp-2026-05-15/ REAL PPP vintage on the UN primary file; supersedes v0.2
  sources/                  committed source extracts (UN WPP 2024 rows, World Bank
                            PA.NUS.PPP 2024 response) + SOURCES.md
  vintages.json             registry: supersedes / superseded_by links, warnings
test_determinism_guard.py   4 determinism invariants (standalone + pytest)
test_vintages.py            backward-compat hash, pinned vintage hashes, FX integrity
test_ppp.py                 PPP leg + population×multiplier weighting
test_cli.py                 CLI end to end
test_anchor.py              anchoring commitment, chaining, tamper detection
test_independent.py         engine × independent-verifier cross-validation
test_properties.py          randomized property / edge / tamper tests (fixed seed)
test_fallbacks.py           data states and fallbacks (stale, suspended, fixed conversion, ...)
test_compat.py              the rename: openunit alias, method names, old vintages unchanged
SPEC.md                     specification
ARTIFACT_FORMAT.md          byte-level spec.json / artifact.json format
docs/ANCHORING.md           anchoring model and external timestamping
```

## On "fairness"

Weighting by population is a **value choice**, not a neutral measurement.
One-person-one-vote favors populous economies; GDP or trade weighting favors
large economies; PPP weighting favors welfare comparisons. Worldyard fixes the
population choice and makes it **contestable**: the method is fixed and
auditable, so the *politics of the weighting* can be argued in public, on the
record, rather than hidden inside an opaque index.

## License

Code: Apache License 2.0 — see [`LICENSE`](LICENSE). Copyright 2026 Hiroshi
Ichiyanagi. Bundled data keep their publishers' terms (see *Scope, licence and
terms* above, `data/sources/SOURCES.md`, and each vintage's `SOURCES.md`).
