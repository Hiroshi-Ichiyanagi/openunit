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
by the bundled v0.2 vintage and by its correction, `v0.4-ppp-unwpp` (method
version `v0.4`: the same formulas, under the v0.3 input domain, with every input
resolved under "Data states and fallbacks" and the resolution recorded in the
spec).

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

## Input domain

The engine validates a basket as follows: every individual `population` must be
**≥ 0**, the **total** population must be **> 0** (so the weights are
well-defined), the total effective weight (population × multiplier) must be
**> 0**, and every FX rate must be **> 0**. Any violation raises `ValueError`
and no artifact is produced.

Rejecting an individual negative `population` was tightened in **v0.3**; earlier
versions accepted a negative value as long as the basket total stayed positive.
The transition is pinned by test (`test_negative_population_is_rejected`) so the
behavior cannot drift silently. All published vintages use only real,
non-negative population data (UN WPP) with positive totals, so this tightening
changes **no** published artifact and **no** hash — it only narrows the accepted
input domain at its previously-undefined edge.

## Data states and fallbacks

openunit never guesses an input. Before a vintage is built, every input — an FX
rate on a date, a population for a year, a PPP factor for a reference year — is
either **resolved** by one of the rules below or it is **unavailable**, and an
unavailable input is never put into a spec. The rules are declared here in
advance and are deterministic: the same observations and the same declared rule
give the same state, value and flags, on any machine, at any time.

Resolution happens **before** the engine runs. `build_artifact` is unchanged and
still takes only resolved numbers, so these rules change no shipped spec,
artifact or hash. The reference implementation is `openunit.resolve_input`
(pure: no I/O, no clock, independent of the order of the observations; tested by
`test_fallbacks.py`).

Scope, stated plainly: these rules make the *treatment* of gaps reproducible and
visible. They do not make a carried-forward or converted number economically
current, and an offline re-check proves only that a past observation was
reproduced, not that it describes today's economy.

### States

| state | meaning | value |
|---|---|---|
| `ok` | an observation exists on the target date | the observation, verbatim |
| `stale` | none on the target date; the latest *earlier* one is within the source's maximum age | that observation, verbatim; flag `STALE`, `age_days` recorded |
| `fixed_conversion` | the currency was replaced by a successor at a fixed conversion rate on or before the target date | successor's resolved value ÷ the fixed rate (exact, precision 50); flag `FIXED_CONVERSION` plus the successor's flags |
| `unavailable` | no rule applies | none (`null`), with a `reason` code |

A later observation never serves an earlier target (no look-ahead), values are
never interpolated or averaged, and no undeclared source is substituted.

### Rules, in order (the first that applies decides)

1. **Extinct currency, fixed conversion.** If the series declares
   `fixed_conversion` and the target is on or after its `effective` date, the
   value is the successor's resolved value divided by `units_per_successor`;
   the old currency's own observations are no longer used, even within the
   maximum age. If the successor is unavailable, so is the input
   (`SUCCESSOR_UNAVAILABLE:<successor's reason>`).
2. **Permanent hole.** If the target is a declared permanent hole →
   `unavailable` (`PERMANENT_HOLE`). A series that declares a hole and also
   carries an observation inside it is malformed.
3. **Suspended rate.** If the target is on or after `suspended_since` →
   `unavailable` (`SUSPENDED`), even within the maximum age.
4. **Retired source.** If the target is on or after `retired_since` →
   `unavailable` (`SOURCE_RETIRED`).
5. **Selection.** Take the observations dated on or before the target,
   restricted to the declared `rate_type` if one is declared. None →
   `unavailable` (`NO_OBSERVATION`).
6. **One value per date.** If more than one remains on the latest date →
   `unavailable` (`AMBIGUOUS_MULTIPLE_RATES`). If a declared `rate_type` picked
   one rate out of several on that date, the result is flagged `MULTIPLE_RATES`.
7. **Age.** `age_days` = target − observation date. Above the source's maximum
   age → `unavailable` (`TOO_OLD`); 0 → `ok`; otherwise `stale`.

### The situations, and the declared rule for each

- **Stale input — maximum age per source.** A target date with no observation
  may be served by the latest earlier observation only within the source's
  maximum age:

  | source | observation date | maximum age |
  |---|---|---|
  | ECB euro reference rates (daily) | reference date | **4 calendar days** |
  | UN World Population Prospects | release date of the revision used | **1461 days** (4 years) before the vintage's weight date |
  | World Bank `PA.NUS.PPP` (annual) | 1 July of the reference year | **1096 days** (3 years) before the valuation date |

  The ECB publishes no rates at weekends or on TARGET closing days (1 January,
  Good Friday, Easter Monday, 1 May, 25 and 26 December); the longest such run
  serves Easter Monday (or 26 December falling on a Tuesday) with a rate 4
  days old, so 4 days is the shortest maximum age that covers every
  closing-day sequence (`test_fallbacks.py` checks this for 2000–2199). The UN
  released WPP 2024 on 11 July 2024 and has postponed its next revision to
  11 July 2027; four years covers that postponement. The three values are
  pre-declared in `openunit.DECLARED_MAX_AGE_DAYS`. A vintage may declare a
  stricter maximum age (it is then hashed with the spec) but never a looser one
  without saying so in its `SOURCES.md`. The shipped vintages use ECB rates on
  their exact dates (age 0), WPP 2024 (547 days before their 2026-01-09
  baseline; 673 days before 2026-05-15, the weight date of v0.2 and v0.4) and,
  for v0.2 and v0.4, `PA.NUS.PPP` 2024 (683 days before 2026-05-15).
- **Suspended or unrepresentative rate.** When the publisher suspends a rate
  because it can no longer set a representative one — the ECB has published no
  euro reference rate for the Russian rouble after 1 March 2022 — the input is
  `unavailable` from the suspension date on. The last rate before the
  suspension is not carried forward. A basket that needs such a currency must
  declare another source, or a different basket, in a new vintage; a
  replacement source must be shown to be independent (a cross rate computed
  from the suspended publisher's own rates is not).
- **Extinct currency with a fixed conversion.** From the effective date, the
  old currency exists only through its successor: Bulgaria joined the euro area
  on 2026-01-01 at BGN 1.95583 = EUR 1 (ECB), so for any later date
  `value(BGN) = value(EUR) / 1.95583`. Before the date, the lev's own rates
  apply. In a basket, the people of the joining economy belong to the
  successor's entry from the effective date (`v0.3-unwpp` counts Bulgaria in
  the euro area).
- **Multiple official or parallel rates.** When a source publishes more than one
  rate for a currency on a date, the spec must declare which `rate_type` it
  uses; the result is flagged `MULTIPLE_RATES` so readers see that a choice was
  made. Without a declared type, or with two values of the declared type on one
  date, the input is `unavailable` (`AMBIGUOUS_MULTIPLE_RATES`). A parallel or
  unofficial rate is used only if a vintage declares it as its source.
- **Permanent data holes.** A period that will never be published is declared
  as a hole and is `unavailable` (`PERMANENT_HOLE`) — it is not interpolated
  and not filled from the neighbouring periods. Example: after the 2025 lapse
  in US appropriations, BLS issued no October 2025 CPI release and did not
  publish October 2025 indexes for most CPI series; it chose not to collect the
  data retroactively. (openunit uses no CPI today; the rule applies to any
  input.)
- **Source endpoint retirement.** A vintage never depends on an endpoint: its
  raw numbers are reproduced in its `SOURCES.md` and hashed in its spec, so it
  stays verifiable offline after a URL disappears. A series is identified by
  publisher, series and definition, not by URL. When the same series moves to a
  new endpoint — the Federal Reserve has announced the eventual retirement of
  the H.10 Data Download Program and directs users to FRED (H.10 release page,
  October 2026) — new vintages record the new URL and check that overlapping
  observations are identical; if they are not, it is a different source and is
  declared as one. When a series stops being published, targets on or after
  `retired_since` are `unavailable` (`SOURCE_RETIRED`).
- **Unavailable instead of guessing.** Every path above that does not end in
  `ok`, `stale` or `fixed_conversion` ends in `unavailable` with a machine-
  readable `reason`. A basket with any unavailable input produces no artifact
  until a new vintage declares how to proceed.

A spec may record how each input was resolved in optional, descriptive keys
(hashed like any other extra key; they change no artifact field). A spec
without such keys asserts that each of its inputs is the latest observation on
or before its date and within the maximum age: for the shipped vintages, FX
rates on their exact dates (`ok`) and population and PPP inputs `stale` by the
ages given above. `v0.4-ppp-unwpp` records its resolution explicitly
(`provenance.input_states`, computed with `resolve_input`).

## Corrections and supersession

- **Originals are never rewritten.** Once a vintage is published, its
  `spec.json`, `artifact.json` and `SOURCES.md` stay byte-identical;
  `test_vintages.py` pins their sha256. (OpenTimestamps proofs live outside
  every hash and may be upgraded, see `docs/ANCHORING.md`.)
- **A correction is a new vintage.** Its spec carries `supersedes`: a list of
  `{"vintage", "artifact_hash", "reasons": [{"code", "detail"}]}`. Because the
  key is part of the spec, the claim is bound to the correction's own
  `input_digest`.
- **The reverse link lives outside the original.** `data/vintages.json` lists
  every vintage with its `artifact_hash`, `status` (`current` or `superseded`),
  `supersedes`, `superseded_by` and machine-readable `warnings`
  (`{"code", "detail"}`, codes in upper case, e.g. `EURO_AREA_MEMBERSHIP`). It
  is part of no hash and is append-only: entries are added; an existing entry
  may only gain `superseded_by` links and warnings. Tests check that the links
  are symmetric and agree with each spec.
- **A superseded vintage still verifies.** Verification proves that an artifact
  reproduces from its spec, not that the spec was right. Anyone relying on a
  vintage should check its entry in `data/vintages.json`.
- **Known issues are warnings.** A vintage with a known problem but no
  corrected successor stays `current` and carries the warning; a superseded
  vintage keeps its warnings. Warnings can also describe a current vintage's
  known limits (e.g. `PPP_EXTRAPOLATED` on `v0.4-ppp-unwpp`).

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
  an ECB nominal-FX baseline, and **World Bank `PA.NUS.PPP` for 2024** for
  USD/CNY/JPY/GBP/INR (`1 openunit = 2.848010 international dollars`). The
  vintage labels these values "ICP 2024"; that is wrong: no ICP 2024 results
  exist yet, and WDI's 2024 values are the ICP 2021 benchmark extrapolated by
  the World Bank (China, India) or Eurostat-OECD annual PPPs (Japan, United
  Kingdom, euro-area members); see `docs/AUDIT.md` (2026-10-26). The World
  Bank publishes **no single Euro-area `PA.NUS.PPP` value**, so the euro-area
  factor is a **population-weighted blend** of the 20 member states,
  `ppp(euro area) = Σ_i pop_i·ppp_i / Σ_i pop_i`, using UN WPP 2024 populations.
  Weighting the blend by people rather than GDP is a deliberate, **contestable**
  value choice consistent with §10; the member table, the formula, and the raw
  World Bank values are reproduced in the vintage's `SOURCES.md`.
- **`v0.3-unwpp-2026-05-15` (REAL; supersedes v0.1).** The v0.1 formulas and
  exactly v0.1's ECB FX inputs, with populations read from the UN Population
  Division's own WPP 2024 file (`WPP2024_Demographic_Indicators_Medium.csv.gz`,
  medium variant, `TPopulation1July` for 2026; CC BY 3.0 IGO) rather than from a
  republication, and the euro area counted on its membership at the valuation
  date (21 states; Bulgaria joined on 2026-01-01). `1 openunit = 0.985654 USD`.
  The 26 rows used are committed as `data/sources/un_wpp2024_population_2026.csv`,
  whose sha256 is part of the spec. v0.1 and v0.2 took the same UN figures from
  Worldometer's republication; 23 of their 25 populations equal the UN file, and
  Greece and Slovenia differ by one person each. v0.1 is not rewritten; the
  correction is recorded in v0.3's hashed spec (`supersedes`) and in
  `data/vintages.json` (`superseded_by`, warnings).
- **`v0.4-ppp-unwpp-2026-05-15` (REAL; supersedes v0.2).** v0.2's PPP-aware
  method (§2.3) with v0.3-unwpp's populations (UN primary file, euro area of 21
  members, in the headcount and in the PPP blend) and the same ECB nominal FX
  as v0.2. The PPP factors are World Bank `PA.NUS.PPP` for 2024 from one API
  response committed verbatim
  (`data/sources/wb_pa_nus_ppp_2024_wdi-2026-10-08.json`, CC BY 4.0, sha256
  part of the spec), labelled as the World Bank labels them: the ICP 2021
  benchmark extrapolated to 2024 (China, India) and Eurostat-OECD annual PPPs
  (Japan, United Kingdom, euro-area members). `1 openunit = 2.845044
  international dollars` (v0.2: 2.848010). Reasons for the correction:
  Bulgaria's membership, the population source, v0.2's "ICP 2024" label, and
  the World Bank's July 2026 revisions of five of v0.2's values.

## 7. Anchoring

The optional anchoring layer (`anchor.py`, `openunit anchor` / `verify-anchor`)
commits an `artifact_hash` to an offline, append-only hash-chain record, so a
publisher can show an artifact existed by a point in time and has not been
silently revised. The core is deterministic, keyless, and offline; an external
public timestamp (OpenTimestamps `.ots` or a chain txid) is attached in a field
outside the commitment. Full model: [`docs/ANCHORING.md`](docs/ANCHORING.md).

## 8. Limitations

- The bundled v0 sample and all illustrative inputs are **non-authoritative**.
- The euro area has **no single published World Bank PPP factor**; v0.2 and
  v0.4 derive it as a population-weighted blend of the member states (20 in
  v0.2, 21 in v0.4). That aggregation is a
  **contestable value choice** (§10), made explicit in the vintage's
  `SOURCES.md` rather than hidden — not a World Bank aggregate.
- The basket is a **subset** of currencies; coverage is a policy choice
  (the bundled basket is the SDR set re-weighted by population, plus India).
- The engine does **not** fetch FX or population; the caller supplies pinned,
  hashed inputs. Provenance lives in each vintage's `SOURCES.md`.
- Nominal-FX vintages (v0.1) understate real command over goods in lower-price
  economies; that is what the PPP leg (v0.2) addresses.
- PPP factors for years after the latest ICP benchmark (2021) are provisional:
  the World Bank extrapolates them for most economies and revises them (it
  revised China and India between its April and July 2026 releases) and will
  replace them when ICP 2024 results are published. A vintage pins the values
  of one release and names it.
- "Equal" weighting is **not** a neutral fact (see §10).

## 9. Roadmap

- Additional real pinned vintages over time (rolling baseline/valuation dates,
  and new PPP reference years as the World Bank publishes them). 2024 was the
  latest `PA.NUS.PPP` year with a value for every basket economy and euro-area
  member when checked on 2026-06-10 (`docs/AUDIT.md`). Those 2024 values are
  not ICP benchmark values: the next ICP benchmark, ICP 2024, has not been
  released, and WDI will replace its extrapolations when it is.
- ✅ A published-artifact **format standard** (`openunit-artifact-1`, see
  `ARTIFACT_FORMAT.md` §9) and a **minimal third-party verifier**
  (`verify_independent.py`, engine-free, stdlib-only).
- ✅ **Public timestamping** for anchors: the shipped vintages carry
  OpenTimestamps proofs confirmed in the Bitcoin blockchain
  (`docs/ANCHORING.md`); the core stays offline.

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
be argued against the exact numbers. `v0.4-ppp-unwpp` makes the same choice
for its 21 members (factor `0.638144`); its GDP-weighted alternative is not
computed, because Bulgaria's GDP was not downloaded.

**Sensitivity (on the record).** The two weightings yield:
population-weighted euro-area `PA.NUS.PPP` `= 0.642950` (**shipped**) vs.
GDP-weighted `= 0.661121` (World Bank `NY.GDP.MKTP.CD`, 2024). Under each, one
openunit in the v0.2 vintage is `2.848010` vs. `2.844627` international dollars —
a ~0.12% difference. openunit ships the **population-weighted** figure
(consistent with the one-person-one-vote stance above); the GDP-weighted
alternative changes no shipped spec, artifact, or hash and is reproduced in full
(member GDP table + formula) in the vintage's `SOURCES.md`.
