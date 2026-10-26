# Changelog

All notable changes to Worldyard (formerly openunit) are documented here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Worldyard is a specification plus a reference implementation; "versions" here refer to **method
versions** (the `method_version` field) and to releases of this repository.

## [0.4.0] — YYYY-MM-DD

### Renamed: openunit is now Worldyard

- **Project, distribution, module and command renamed to `worldyard`**
  (`pyproject.toml` name `worldyard`, version `0.4.0.dev0`; engine module
  `worldyard.py`; console script `worldyard`). Entries for 0.3.0 and earlier
  below keep the old names.
- **Nothing that was published changes.** The method name is part of every
  hash (`method` in the spec and in the artifact), so vintages built before
  the rename (v0.1, v0.2, v0.3-unwpp) keep `"openunit"` and every byte and
  hash; only new vintages (from `v0.4-ppp-unwpp`) carry `"worldyard"`. The
  engine and the independent verifier copy `method` from the spec, accept
  `"openunit"` (also the meaning of an absent `method`) and `"worldyard"`, and
  reject anything else.
- **Format standard `worldyard-artifact-2`** (`ARTIFACT_FORMAT.md`): the only
  change from `openunit-artifact-1` is the `method` field. Every `-1` artifact
  is a `-2` artifact with the same bytes; the published `-1` verifier still
  passes v0.1 to v0.3 but reports `method` and `artifact_hash` as differing on
  a `"worldyard"` vintage.
- Kept as wire identifiers: the anchor record version `openunit-anchor-1`
  (part of every anchor commitment) and the registry format
  `openunit-vintage-registry-1`.
- The GitHub repository and the URLs in `pyproject.toml` keep the old name
  until the repository is renamed; the URLs will be updated then.

### Deprecated

- `import openunit`: still works, emits a `DeprecationWarning`, and returns the
  `worldyard` module itself (same functions and constants). `python3
  openunit.py` still runs the demo.
- The `openunit` command (`cli:main_openunit`): same subcommands, plus a
  notice on stderr.
- If the old distribution is installed, run `pip uninstall openunit` before
  `pip install -e .`: both distributions provide the same modules and the
  `openunit` command.

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
- **New vintage `v0.4-ppp-unwpp-2026-05-15`** (method `worldyard`, method
  version `v0.4`, `artifact_hash` `sha256:d0fa4776…e175`, `1 worldyard =
  2.845044 international dollars`; v0.2: 2.848010, −0.104 %): v0.2's PPP-aware method with
  v0.3-unwpp's UN populations and 21-member euro area (headcount and PPP
  blend; euro-area factor 0.638144, v0.2: 0.642950), v0.2's ECB nominal FX,
  and World Bank `PA.NUS.PPP` 2024 from one API response committed verbatim
  (`data/sources/wb_pa_nus_ppp_2024_wdi-2026-10-08.json`, 7316 bytes, sha256
  `b4db34d4…ed0d`, CC BY 4.0, retrieved 2026-10-26, WDI last updated
  2026-10-08). Each factor is labelled as the World Bank labels it (ICP 2021
  extrapolation for China and India, Eurostat-OECD annual PPP otherwise), and
  the spec records each input's state under "Data states and fallbacks"
  (`provenance.input_states`). It declares in its hashed spec that it
  **supersedes** `v0.2-ppp-2026-05-15` (reasons `EURO_AREA_MEMBERSHIP`,
  `POPULATION_VIA_REPUBLISHER`, `POPULATION_MISMATCH`, `PPP_LABEL`,
  `PPP_REVISED`); v0.2 becomes `superseded` in `data/vintages.json` and v0.4
  carries the warning `PPP_EXTRAPOLATED`.
- `data/vintages.json`: append-only registry of supersedes / superseded_by
  links and machine-readable warnings (v0.1: superseded; v0.2: current with
  warnings).
- Tests: published v0.1/v0.2 files pinned by sha256 (never rewritten); v0.3
  populations = UN extract; v0.3 FX = v0.1 FX; registry consistency; v0.4
  populations = v0.3's, PPP factors = the pinned response's exact tokens,
  euro-area blend recomputed, labels follow the World Bank's footnotes,
  input states re-resolved; `test_compat.py` for the rename (alias module and
  command, method names in both implementations, old vintages unchanged).
- **`SPEC.md` "Data states and fallbacks"**: pre-declared, deterministic rules
  for stale inputs (maximum age per source: ECB 4 days, UN WPP 1461 days, World
  Bank PPP 1096 days), suspended rates (ECB RUB), extinct currencies with a
  fixed conversion (BGN 1.95583 = EUR 1 from 2026-01-01), multiple official /
  parallel rates (declared `rate_type` + `MULTIPLE_RATES` flag), permanent data
  holes (BLS October 2025 CPI), source endpoint retirement (Fed H.10 Data
  Download Program), and an explicit `unavailable` state with a reason code.
- **`worldyard.resolve_input`**: the pure, deterministic implementation (no
  clock, no I/O, order-independent; not called by `build_artifact`, so no
  artifact or hash changes) and `worldyard.DECLARED_MAX_AGE_DAYS`.
  `test_fallbacks.py` covers every state, the precedence order, validation, and
  proves the ECB maximum age is the tightest value covering every TARGET
  closing-day run in 2000–2199.
- **`SPEC.md` "Corrections and supersession"**: originals never rewritten;
  corrections as new vintages with a hashed `supersedes`; reverse links and
  warnings in the append-only `data/vintages.json`.

### Changed

- `make verify-independent` and CI iterate over `data/*/spec.json`, so the
  non-vintage `data/sources/` directory is skipped.
- The demo and `worldyard build` print the artifact's own method name
  ("1 openunit = …" for vintages built before the rename); `show` prints
  "1 unit".
- PPP vintages (v0.2, v0.4) are printed in "international $" by `show`,
  `build`, the demo and `verify_independent.py` (display only); their hashed
  `numeraire` field stays `USD` (`SPEC.md` §2.3).

### Found (no published file changed)

- v0.1 and v0.2 count **20** euro-area members; on their FX dates the euro area
  had **21** (Bulgaria from 2026-01-01). 23 of their 25 Worldometer-sourced
  populations equal the UN file; Greece and Slovenia differ by one person.
- **v0.2's "ICP 2024" label is wrong.** No ICP 2024 results have been released
  (the latest ICP cycle is 2021, released May 2024). WDI's `PA.NUS.PPP` values
  for 2024 are the ICP 2021 benchmark extrapolated by the World Bank (China,
  India) and Eurostat-OECD annual PPPs (Japan, United Kingdom, euro-area
  members). v0.2's 25 values equal WDI's April 2026 release; the July 2026
  release revised five of them (China −0.203 %, India +0.148 %, Croatia,
  Cyprus and Malta by 0.0003 % or less). Recorded in `docs/AUDIT.md` and as
  `PPP_LABEL` / `PPP_REVISED` warnings in `data/vintages.json`; the published
  v0.2 files are unchanged.

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
