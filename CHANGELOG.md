# Changelog

All notable changes to openunit are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). openunit is a
specification plus a reference implementation; "versions" here refer to **method
versions** (the `method_version` field) and to releases of this repository.

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
