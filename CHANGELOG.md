# Changelog

All notable changes to openunit are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). openunit is a
specification plus a reference implementation; "versions" here refer to **method
versions** (the `method_version` field) and to releases of this repository.

## [Unreleased] — draft on branch `feat/v0.4-sources-fallbacks` (not published)

### Added

- **New vintage `v0.3-unwpp-2026-05-15`** (`artifact_hash`
  `sha256:0fe13c83…b7af`, `1 openunit = 0.985654 USD`): v0.1's formulas and
  exactly v0.1's ECB FX, with populations read from the UN Population
  Division's own WPP 2024 file (`WPP2024_Demographic_Indicators_Medium.csv.gz`,
  16557272 bytes, sha256 `286ac36b…82bc`, CC BY 3.0 IGO, retrieved 2026-10-26)
  and the euro area on its 2026-05-15 membership (21 states; Bulgaria joined on
  2026-01-01). It declares in its hashed spec that it **supersedes**
  `v0.1-2026-05-15`.
- `data/sources/un_wpp2024_population_2026.csv`: the 26 UN rows used (verbatim
  plus a derived persons column), pinned by sha256; `make_vintages.py
  --check-un-wpp RAW` re-derives it from the raw UN file byte for byte.
- `data/vintages.json`: append-only registry of supersedes / superseded_by
  links and machine-readable warnings (v0.1: superseded; v0.2: current with
  warnings).
- Tests: published v0.1/v0.2 files pinned by sha256 (never rewritten); v0.3
  populations = UN extract; v0.3 FX = v0.1 FX; registry consistency.
- **`SPEC.md` "Data states and fallbacks"**: pre-declared, deterministic rules
  for stale inputs (maximum age per source: ECB 4 days, UN WPP 1461 days, World
  Bank PPP 1096 days), suspended rates (ECB RUB), extinct currencies with a
  fixed conversion (BGN 1.95583 = EUR 1 from 2026-01-01), multiple official /
  parallel rates (declared `rate_type` + `MULTIPLE_RATES` flag), permanent data
  holes (BLS October 2025 CPI), source endpoint retirement (Fed H.10 Data
  Download Program), and an explicit `unavailable` state with a reason code.
- **`openunit.resolve_input`**: the pure, deterministic implementation (no
  clock, no I/O, order-independent; not called by `build_artifact`, so no
  artifact or hash changes) and `openunit.DECLARED_MAX_AGE_DAYS`.
  `test_fallbacks.py` (written first, 26/26 failing before the
  implementation) covers every state, the precedence order, validation, and
  proves the ECB maximum age is the tightest value covering every TARGET
  closing-day run in 2000–2199.
- **`SPEC.md` "Corrections and supersession"**: originals never rewritten;
  corrections as new vintages with a hashed `supersedes`; reverse links and
  warnings in the append-only `data/vintages.json`.

### Changed

- `make verify-independent` and CI iterate over `data/*/spec.json`, so the
  non-vintage `data/sources/` directory is skipped.

### Found (no published file changed)

- v0.1 and v0.2 count **20** euro-area members; on their FX dates the euro area
  had **21** (Bulgaria from 2026-01-01). 23 of their 25 Worldometer-sourced
  populations equal the UN file; Greece and Slovenia differ by one person.

## [0.3.0] — 2026-06-14

### Added

- **Published-artifact format standard `openunit-artifact-1`** (`ARTIFACT_FORMAT.md`
  §9): a normative conformance definition and a version identifier for the byte
  layout, naming `verify_independent.py` as the minimal third-party verifier /
  conformance oracle. `SPEC.md` roadmap marks the format-standard and public
  (Bitcoin) timestamping items delivered.

### Changed

- **Input domain tightened: negative populations are now rejected.** The engine
  (`openunit._compute`) raises `ValueError` on any individual `population < 0`,
  closing the previously-undefined edge where a negative value was accepted as
  long as the basket total stayed positive. The independent verifier
  (`verify_independent.py`) rejects it identically. Because every published
  vintage uses real, non-negative UN WPP populations with positive totals, **no
  published artifact or hash changes** (v0.1 `sha256:1e615cf7…9a3a`, v0.2
  `sha256:566c95c1…b97a`, v0 sample `sha256:433d5e95…56bd` all unchanged). The
  characterization test that pinned the old behavior is replaced by
  `test_negative_population_is_rejected`, which pins the new contract. `SPEC.md`
  ("Input domain") updated accordingly.

## [0.2.2] — 2026-06-13

### Added

- **Independent second-implementation verifier** (`verify_independent.py`):
  re-verifies an artifact against its spec from `SPEC.md` / `ARTIFACT_FORMAT.md`
  alone, never importing `openunit`/`cli`/`anchor`. Standard library only;
  exit 0 iff every field and both hashes match. Wired into `make verify`, a new
  `make verify-independent` target, and CI (all OSes).
- **Property / edge tests** (`test_properties.py`): randomized valid baskets
  (fixed seed, test-only `random`) check byte-identical rebuilds, weight/baseline
  invariants within rounding tolerance, agreement with the independent
  recomputation, single-character tamper rejection, and canonical key-order
  invariance vs. basket-order sensitivity. Edge tests freeze current engine
  behavior for non-positive total population / FX (rejected) and negative
  per-entry population with a positive total (currently accepted — characterized
  honestly, not changed).
- **Cross-validation tests** (`test_independent.py`): the engine's artifacts are
  checked by the engine-free verifier across every vintage, the v0 sample, and
  the multiplier branch, with tamper/spec-mismatch rejection.
- `test_vintages.py` now pins each shipped vintage's `artifact_hash` and asserts
  no unpinned vintage ships.

### Changed

- **Verbatim ECB strings.** Two valuation-leg rates transcribed in
  `make_vintages.py` carried a cosmetic trailing zero (`GBP 0.87050`,
  `INR 111.5940`); they are normalized to the exact official ECB XML strings
  (`0.8705`, `111.594`). **Numbers are unchanged** (`1 openunit = 0.985631 USD`),
  but the raw strings are part of the v0.1 hashed spec, so the **v0.1 hashes
  change**: `artifact_hash sha256:82bade1f…9655 → sha256:1e615cf7…9a3a`
  (`input_digest sha256:495f80f2…a80a → sha256:90b54dc5…fe25`). The v0.2 vintage
  (`sha256:566c95c1…b97a`) and the v0 sample (`sha256:433d5e95…56bd`) are
  unchanged. Documented in `docs/AUDIT.md` (addendum). Engine code is untouched.
- Docs: disclose input-domain limitation — a negative individual population
  value is currently accepted when the basket total is positive (pinned by
  test); rejection planned for v0.3.

## [0.2.1] — 2026-06-09

### Changed

- **The v0.2 PPP vintage now uses real World Bank `PA.NUS.PPP` (ICP 2024)** for
  USD/CNY/JPY/GBP/INR, replacing the illustrative factors. The World Bank
  publishes **no single Euro-area `PA.NUS.PPP` value**, so the euro-area factor
  is a **population-weighted blend** of the 20 member states
  (`Σ pop_i·ppp_i / Σ pop_i`, UN WPP 2024 populations); that aggregation is
  documented as a contestable, one-person-one-vote choice (`SPEC.md` §10), not
  removed. Vintage renamed `v0.2-ppp-illustrative-2026-05-15` →
  `v0.2-ppp-2026-05-15`; `1 openunit = 2.848010 international dollars`,
  `artifact_hash sha256:566c95c1…b97a`. The illustrative factors and the
  "PPP data illustrative" caveat are gone.

## [0.2.0] — 2026-06-08

### Added

- **Method v0.2 (PPP-aware).** Population weights with a PPP valuation leg, so
  the unit can be read in international dollars; `realized_weight_at_valuation`
  exposes the shift of effective weight toward lower-price economies.
- **Optional `weight_multiplier`** per basket entry, generalizing the weighting
  (`effective_weight ∝ population × multiplier`) while keeping
  `population_share` as the pure headcount share. Emitted only when present, so
  plain v0 specs stay byte-for-byte identical (backward compatible).
- **Command-line interface** (`cli.py` / `openunit`): `build`, `verify`,
  `show`, `anchor`, `verify-anchor`.
- **Anchoring** (`anchor.py`): offline, keyless, deterministic hash-chain
  commitment over an `artifact_hash`, with an `external_proof` slot (outside the
  commitment) for public timestamps. Documented in `docs/ANCHORING.md`.
- **Pinned data vintages** under `data/`: `v0.1-2026-05-15` (REAL) and
  `v0.2-ppp-illustrative-2026-05-15` (PPP mechanism, illustrative factors), each
  with `spec.json`, `artifact.json`, and `SOURCES.md`.
- **`make_vintages.py`** to regenerate the vintages, with a `--verify` mode that
  recomputes them in memory and compares to disk (nonzero exit on mismatch).
- Tests: `test_vintages.py`, `test_ppp.py`, `test_cli.py`, `test_anchor.py`.
- Documentation: `ARTIFACT_FORMAT.md`, `docs/ANCHORING.md`; packaging
  (`pyproject.toml`); CI (`.github/workflows/ci.yml`); community files.

## [0.1.0] — 2026-06-08

### Added

- **Method v0.1 (real data).** Same one-person-one-vote method as v0, on real
  inputs: UN World Population Prospects 2024 and ECB euro reference rates.
  First vintage that asserts a real value: `1 openunit = 0.985631 USD`
  (`v0.1-2026-05-15`).

## [0.0.0] — 2026-06-08

### Added

- **Method v0.** Deterministic, population-weighted unit of account: engine
  (`openunit.py`) with `build_artifact` / `verify_artifact`, the SDR-style
  fixed-basket mechanism, exact `Decimal` arithmetic, canonical-JSON SHA-256
  hashing, and the determinism guard (`test_determinism_guard.py`).
- Illustrative, explicitly non-authoritative `sample_input.json`, pinned to
  `artifact_hash sha256:433d5e95…56bd` (backward-compatibility anchor).
- `SPEC.md` (method, determinism, format, verification, fairness).
