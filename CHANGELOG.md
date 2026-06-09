# Changelog

All notable changes to openunit are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). openunit is a
specification plus a reference implementation; "versions" here refer to **method
versions** (the `method_version` field) and to releases of this repository.

## [Unreleased]

- Real, verified PPP vintage (World Bank `PA.NUS.PPP`, with a documented
  euro-area aggregation rule), replacing the illustrative v0.2 factors.

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
