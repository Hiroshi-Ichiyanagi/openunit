# Contributing to openunit

Thanks for your interest. openunit is small on purpose, and its whole value is
that **anyone can recompute the same numbers and the same hashes, byte for
byte.** Contributions are welcome as long as they preserve that property.

> Don't trust me. Verify me.

## Ground rules (non-negotiable, because they are the product)

1. **Standard library only.** No third-party runtime dependencies. `pytest` is
   used for tests but the suites also run standalone with plain `python3`.
2. **Determinism.** No wall-clock reads (`datetime`/`time`), no randomness, no
   network or filesystem access inside the engine. Numbers are exact
   `decimal.Decimal` parsed from **strings**, at precision 50 / ROUND_HALF_EVEN,
   inside an isolated `localcontext`.
3. **Backward compatibility.** The bundled v0 sample must keep
   `artifact_hash sha256:433d5e95…56bd`. Adding a field to artifacts must not
   change the bytes of specs that do not use it (see the conditional emission of
   `weight_multiplier` / `effective_weight`).
4. **Honesty about data.** Illustrative inputs must be clearly labelled
   non-authoritative. A vintage may claim a real value only if every input is
   transcribed from a named public source and recorded in its `SOURCES.md`.

## Running the checks

```sh
python3 test_determinism_guard.py     # 4 invariants, standalone
python3 make_vintages.py --verify     # vintages reproduce, byte for byte
python3 -m pytest -q                  # full suite (22 tests)
```

`make verify` and `make test` wrap these (see the `Makefile`). CI runs the same
on every push and pull request across supported Python versions.

## Adding or updating a data vintage

1. Put the raw, as-published source numbers in `make_vintages.py` (do not
   pre-divide; let the exact arithmetic derive the engine inputs).
2. Record provenance — source name, URL, date retrieved, raw values, and the
   exact conversion — in the vintage's `SOURCES.md`. Reproduce the raw rates in
   the file so the vintage stays verifiable independently of any live feed.
3. Run `python3 make_vintages.py` to write `spec.json`, `artifact.json`, and
   `SOURCES.md`, then `python3 make_vintages.py --verify` to confirm
   reproduction.
4. If the new vintage should be pinned against regression, add its hash to
   `test_vintages.py`.

## Commits and pull requests

- Keep changes focused; explain *why* in the description.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Make sure all checks pass locally before opening a PR.

By contributing you agree your contributions are licensed under the project's
Apache-2.0 license.
