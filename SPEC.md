# openunit — Specification

openunit is a deterministic, publicly verifiable, **population-weighted unit of
account**. It does not issue money and it does not settle payments. It only
*measures*: given a pinned set of inputs, anyone can recompute the exact same
value and the exact same hashes, byte for byte.

> Don't trust me. Verify me.

This document specifies the method, the determinism guarantees, the on-disk
formats, and the verification procedure. The byte-level field layout lives in
[`ARTIFACT_FORMAT.md`](ARTIFACT_FORMAT.md); the anchoring model lives in
[`docs/ANCHORING.md`](docs/ANCHORING.md).

## 1. Purpose and non-goals

**Purpose.** Provide a neutral, transparent way to express value that counts
*people* equally rather than privileging whichever country issues the reserve
currency. The reference value is reported in a numeraire (USD here) only as a
readable denomination; the *unit itself* is defined by the basket, not by any
single national currency.

**Non-goals.** openunit is not a currency, token, stablecoin, or settlement
rail. It does not predict returns and gives no financial advice. A vintage
asserts a real-world value only when it is built from real, named, pinned, and
hashed inputs (see §6); the bundled `sample_input.json` is illustrative and
explicitly non-authoritative.

## 2. Mechanism

Three independent design choices:

1. **One person, one vote.** For each basket entry *i*,
   `weight_i = population_i / Σ_j population_j`.
2. **Frequency separation.** Weights are pinned at a low-frequency *vintage*
   (annual / multi-year). Value is read from a separate, higher-frequency leg
   (e.g. daily market FX, or a PPP leg). The two cadences never mix inside a
   single computation.
3. **Vintage pinning (fixed basket).** This is the **population version of the
   SDR method**: at the vintage a fixed *quantity* of each currency is pinned,
   not its weight. As the valuation leg moves, realized weights drift; the
   pinned weights are restated only at the next vintage.

### 2.1 Formulas

Let `fx_b_i` be the baseline rate (numeraire per 1 unit of currency *i*, captured
at the weight vintage) and `fx_v_i` the valuation-leg rate.

```
weight_i        = population_i / Σ_j population_j               # pinned
amount_i        = weight_i / fx_b_i                             # fixed quantity
baseline_value  = Σ_i amount_i · fx_b_i        ( = 1 by construction )
value(openunit) = Σ_i amount_i · fx_v_i                         # 1 openunit, in numeraire
realized_weight_at_pin_i        = amount_i · fx_b_i / baseline_value     ( = weight_i )
realized_weight_at_valuation_i  = amount_i · fx_v_i / value(openunit)
```

### 2.2 Optional weighting multiplier

A basket entry may carry an optional `weight_multiplier` *m_i* (default `"1"`),
which generalizes the weighting while keeping headcount visible:

```
effective_weight_i = (population_i · m_i) / Σ_j (population_j · m_j)
amount_i           = effective_weight_i / fx_b_i
population_share_i = population_i / Σ_j population_j        # always pure headcount
```

When **no** entry carries a multiplier, the artifact is byte-for-byte identical
to plain v0 (the `weight_multiplier` / `effective_weight` fields are *not*
emitted). This is what preserves backward compatibility (§4.3). The multiplier
is the mechanism behind the alternative "population × PPP weighting"
interpretation; the bundled v0.2 vintage instead uses the **valuation-leg**
interpretation (§2.3), and the multiplier path is exercised by `test_ppp.py`.

### 2.3 PPP-aware valuation (v0.2)

PPP awareness can enter through the **valuation leg** rather than the weights:
keep one-person-one-vote weights, set the baseline leg to nominal market FX, and
set the valuation leg to a PPP rate (international dollars per unit,
`= 1 / PPP_factor`). The unit is then read in international dollars, and
`realized_weight_at_valuation` shows how real purchasing power redistributes
effective weight toward lower-price economies. This is the interpretation used
by the bundled v0.2 vintage.

## 3. Determinism

- **stdlib only** (`json`, `hashlib`, `decimal`).
- **Exact arithmetic** with `decimal.Decimal`, precision **50**, rounding
  **ROUND_HALF_EVEN**, inside an isolated `localcontext` (the caller's global
  context is never modified). All numeric inputs are parsed from **strings**,
  never from floats.
- **No wall clock.** The implementation never imports or calls `datetime` or
  `time`; the result depends only on the inputs, never on when it runs.
- **Canonical encoding** for every hash: `json.dumps(obj, sort_keys=True,
  separators=(",", ":"), ensure_ascii=False)` encoded as UTF-8.
- **Hashes** (SHA-256, prefixed `sha256:`):
  - `input_digest`  = hash of the canonical **spec**.
  - `artifact_hash` = hash of the canonical **artifact minus `artifact_hash`**.

These invariants are enforced by `test_determinism_guard.py`: identical input →
identical output (including a JSON round-trip), absence of any wall-clock read
(by source scan *and* by poisoning `time.*` at runtime), tamper detection, and
pinned realized weights equal to population shares at precision 60.

## 4. Spec and artifact format

### 4.1 Spec (input)

A spec is a JSON object with: `method` (`"openunit"`), `method_version`
(`"v0"`, `"v0.1"`, `"v0.2"`, …), `numeraire`, a `weight_vintage` object
(`label`, `basis`, and free-form provenance), and a `basket` array. Each basket
entry has `code`, optional `name`, `population` (decimal string),
`fx_baseline_usd_per_unit`, `fx_valuation_usd_per_unit`, and optionally
`weight_multiplier`. Additional descriptive keys (provenance, disclaimers, raw
source rates) are permitted and are hashed as part of the spec. All numbers are
decimal **strings**.

### 4.2 Artifact (output)

| field | meaning |
|---|---|
| `method`, `method_version` | `"openunit"`, e.g. `"v0.1"` |
| `numeraire` | denomination of `value_usd` (e.g. `"USD"`) |
| `weight_vintage_label` | label of the pinned weight vintage |
| `weight_basis` | e.g. `"population_share"` |
| `baseline_value_usd` | value at the baseline leg (= 1 by construction) |
| `value_usd` | value of 1 openunit at the valuation leg |
| `basket[]` | per entry: `code`, `name`, `population_share`, `fixed_amount`, `realized_weight_at_pin`, `realized_weight_at_valuation` (and, only if multipliers are present, `weight_multiplier`, `effective_weight`) |
| `input_digest` | SHA-256 of the spec |
| `artifact_hash` | SHA-256 of the artifact excluding this field |

All numbers are stored as exact decimal **strings**. The precise byte-level
rules are in [`ARTIFACT_FORMAT.md`](ARTIFACT_FORMAT.md).

### 4.3 Backward compatibility

A spec whose entries carry no `weight_multiplier` produces output that is
byte-for-byte identical to openunit v0. The bundled illustrative v0 sample is
pinned in `test_vintages.py` to `artifact_hash`
`sha256:433d5e95…56bd` and must not regress.

## 5. Verification

`verify_artifact(artifact, spec)` returns `True` iff **all** hold:

1. `artifact.input_digest == sha256(canonical(spec))` — the artifact is paired
   with this spec;
2. `sha256(canonical(artifact \ artifact_hash)) == artifact.artifact_hash` —
   internal integrity;
3. rebuilding from `spec` reproduces `artifact` exactly.

Any single-field tamper breaks (2) and/or (3). From the command line:
`openunit verify artifact.json spec.json` (exit 0 on success, 1 on failure).

## 6. Reference vintages

Bundled under `data/`, each with `spec.json`, `artifact.json`, and `SOURCES.md`.
Regenerate or check them with `python3 make_vintages.py [--verify]`.

- **`v0.1-2026-05-15` (REAL).** One person, one vote on real inputs: UN World
  Population Prospects 2024 (2026 estimate) and ECB euro reference rates
  (baseline `2026-01-09`, valuation `2026-05-15`). `1 openunit = 0.985631 USD`.
  The euro area is the sum of its 20 member states; the USD numeraire rate for
  each currency is `usd_per_unit(C) = (USD per EUR) / (C per EUR)`. The raw ECB
  rates are reproduced in `SOURCES.md` so the vintage stays verifiable
  independently of the live feed.
- **`v0.2-ppp-2026-05-15` (REAL).** Population weights with a PPP valuation leg
  (§2.3), read in international dollars. Inputs are real and named: UN WPP 2024,
  an ECB nominal-FX baseline, and **World Bank `PA.NUS.PPP` (ICP 2024)** for
  USD/CNY/JPY/GBP/INR (`1 openunit = 2.848010 international dollars`). The World
  Bank publishes **no single Euro-area `PA.NUS.PPP` value**, so the euro-area
  factor is a **population-weighted blend** of the 20 member states,
  `ppp(euro area) = Σ_i pop_i·ppp_i / Σ_i pop_i`, using UN WPP 2024 populations.
  Weighting the blend by people rather than GDP is a deliberate, **contestable**
  value choice consistent with §10; the member table, the formula, and the raw
  World Bank values are reproduced in the vintage's `SOURCES.md`.

## 7. Anchoring

The optional anchoring layer (`anchor.py`, `openunit anchor` / `verify-anchor`)
commits an `artifact_hash` to an offline, append-only hash-chain record, so a
publisher can show an artifact existed by a point in time and has not been
silently revised. The core is deterministic, keyless, and offline; an external
public timestamp (OpenTimestamps `.ots` or a chain txid) is attached in a field
outside the commitment. Full model: [`docs/ANCHORING.md`](docs/ANCHORING.md).

## 8. Limitations

- The bundled v0 sample and all illustrative inputs are **non-authoritative**.
- The euro area has **no single published World Bank PPP factor**; v0.2 derives
  it as a population-weighted blend of the member states. That aggregation is a
  **contestable value choice** (§10), made explicit in the vintage's
  `SOURCES.md` rather than hidden — not a World Bank aggregate.
- The basket is a **subset** of currencies; coverage is a policy choice
  (the bundled basket is the SDR set re-weighted by population, plus India).
- The engine does **not** fetch FX or population; the caller supplies pinned,
  hashed inputs. Provenance lives in each vintage's `SOURCES.md`.
- Nominal-FX vintages (v0.1) understate real command over goods in lower-price
  economies; that is what the PPP leg (v0.2) addresses.
- "Equal" weighting is **not** a neutral fact (see §10).

## 9. Roadmap

- Additional real pinned vintages over time (rolling baseline/valuation dates,
  and new ICP years for the PPP leg as the World Bank publishes them).
- A published-artifact **format standard** and a minimal third-party verifier.
- Optional **public timestamping** recipes for anchors (the core stays offline).

## 10. On "fairness"

Choosing to weight by population is a **value choice**, not a neutral
measurement. One-person-one-vote favors populous economies; GDP or trade
weighting favors large economies; PPP weighting favors welfare comparisons.
openunit makes the population choice explicit and **contestable**: the method is
fixed and auditable, so the *politics of the weighting* can be argued in the
open, on the record, rather than hidden inside an opaque index.

The v0.2 euro-area PPP factor is a concrete instance: because the World Bank
publishes no single Euro-area `PA.NUS.PPP` value, openunit blends the 20 member
states **weighted by population** rather than by GDP. That is the same value
choice applied one level down — recorded in the vintage's `SOURCES.md` with the
full member table and formula so a GDP-weighted (or any other) alternative can
be argued against the exact numbers.

**Sensitivity (on the record).** The two weightings yield:
population-weighted euro-area `PA.NUS.PPP` `= 0.642950` (**shipped**) vs.
GDP-weighted `= 0.661121` (World Bank `NY.GDP.MKTP.CD`, 2024). Under each, one
openunit in the v0.2 vintage is `2.848010` vs. `2.844627` international dollars —
a ~0.12% difference. openunit ships the **population-weighted** figure
(consistent with the one-person-one-vote stance above); the GDP-weighted
alternative changes no shipped spec, artifact, or hash and is reproduced in full
(member GDP table + formula) in the vintage's `SOURCES.md`.
