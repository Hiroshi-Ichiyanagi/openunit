# openunit

A deterministic, publicly verifiable, **population-weighted unit of account**.

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Dependencies](https://img.shields.io/badge/dependencies-none%20(stdlib)-success.svg)

openunit is a *measuring stick*, not money. It does not issue a currency, hold
reserves, or settle payments. It defines one thing precisely: a unit of value
whose basket weights count **people**, not whichever country issues the reserve
currency — and it does so reproducibly, so anyone can recompute the exact same
number and the exact same hashes, byte for byte.

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

## Why

Expressing value in a single national currency bakes in the politics of who
issues it. openunit counts people equally instead: one person, one vote. That
is deliberately a **value choice, not a neutral fact** (see *On "fairness"*
below and `SPEC.md` §10) — the point is to make the choice explicit, fixed, and
auditable so it can be argued in the open rather than hidden inside an opaque
index.

## Quickstart

```sh
git clone <repo-url> openunit && cd openunit
python3 test_determinism_guard.py     # 4/4 determinism checks
python3 make_vintages.py --verify     # real vintages reproduce, byte for byte
python3 openunit.py                    # illustrative demo
```

No third-party dependencies — Python **3.8+** standard library only.

## The reference vintages

Two pinned vintages ship under `data/`. Each has a `spec.json` (the hashed
input), an `artifact.json` (the built, self-verifying result), and a
`SOURCES.md` (full provenance: URLs, dates, raw numbers, and the exact
conversion used).

### `v0.1-2026-05-15` — **REAL DATA**

Method v0.1 (one person, one vote) on real, named inputs.

- inputs: UN **World Population Prospects 2024** (2026 estimate) + **ECB euro
  reference rates** (baseline `2026-01-09`, valuation `2026-05-15`)
- **1 openunit = 0.985631 USD**
- `artifact_hash` `sha256:1e615cf7…9a3a`
- population-pinned weights: India 39.08 %, China 37.39 %, United States
  9.24 %, euro area 9.20 %, Japan 3.24 %, United Kingdom 1.85 %

### `v0.2-ppp-2026-05-15` — **REAL DATA (World Bank `PA.NUS.PPP`, ICP 2024)**

Method v0.2 (population weights, PPP valuation leg) on real, named inputs: UN
**World Population Prospects 2024** + an **ECB** nominal-FX baseline + **World
Bank `PA.NUS.PPP`** (ICP 2024) on the valuation leg, so the unit is read in
**international dollars**.

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

## Command-line interface

```sh
openunit build  spec.json -o artifact.json     # build + self-verify
openunit verify artifact.json spec.json         # exit 0 iff it reproduces
openunit show   artifact.json                   # one-screen summary
openunit anchor artifact.json -o anchor.json [--prev prev.json] [--label L]
openunit verify-anchor anchor.json artifact.json [--prev prev.json]
```

After a local install (`pip install -e .`) the `openunit` command is available;
otherwise run the same subcommands with `python3 cli.py …`.

## Verifying someone else's published value

You need exactly two files: the `spec.json` that was hashed and the
`artifact.json` that was published.

```sh
openunit verify artifact.json spec.json
```

`verify` returns success only if **all three** hold: the artifact's
`input_digest` matches the spec, the artifact's `artifact_hash` matches its own
content, and rebuilding from the spec reproduces the artifact exactly. Any
single-field edit to either file breaks verification. See `SPEC.md` §5.

## Independent verification (don't even trust the engine)

`openunit verify` uses the engine to check the engine's own output. If you do
not want to extend even that much trust, `verify_independent.py` is a **second
implementation** of the entire verification procedure, written from `SPEC.md`
and `ARTIFACT_FORMAT.md` alone: it never imports `openunit`/`cli`/`anchor` and
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

## Determinism guarantees

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

openunit's value is reproducibility, not authority. The optional anchoring
helper commits an `artifact_hash` to a small, offline, append-only hash-chain
record so a publisher can say "this exact artifact existed by this point and has
not been silently revised." Producing a public, independently-checkable
timestamp (an OpenTimestamps `.ots` proof or a blockchain txid) is an *external*
step and is carried in a field that is **not** part of the commitment, so it can
be attached later without changing any hash. See `docs/ANCHORING.md`.

## Project layout

```
openunit.py                 engine: build_artifact / verify_artifact (+ demo)
cli.py                      command-line interface
anchor.py                   tamper-evident anchoring (offline hash-chain)
make_vintages.py            regenerate / --verify the pinned data vintages
verify_independent.py       independent second-implementation verifier (no engine import)
sample_input.json           illustrative v0 spec (non-authoritative)
data/
  v0.1-2026-05-15/          REAL vintage: spec.json, artifact.json, SOURCES.md
  v0.2-ppp-2026-05-15/      REAL PPP vintage: World Bank PA.NUS.PPP (ICP 2024)
test_determinism_guard.py   4 determinism invariants (standalone + pytest)
test_vintages.py            backward-compat hash, pinned vintage hashes, FX integrity
test_ppp.py                 PPP leg + population×multiplier weighting
test_cli.py                 CLI end to end
test_anchor.py              anchoring commitment, chaining, tamper detection
test_independent.py         engine × independent-verifier cross-validation
test_properties.py          randomized property / edge / tamper tests (fixed seed)
SPEC.md                     specification
ARTIFACT_FORMAT.md          byte-level spec.json / artifact.json format
docs/ANCHORING.md           anchoring model and external timestamping
```

## On "fairness"

Weighting by population is a **value choice**, not a neutral measurement.
One-person-one-vote favors populous economies; GDP or trade weighting favors
large economies; PPP weighting favors welfare comparisons. openunit fixes the
population choice and makes it **contestable**: the method is fixed and
auditable, so the *politics of the weighting* can be argued in public, on the
record, rather than hidden inside an opaque index.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE). Copyright 2026 Hiroshi Ichiyanagi.
