# openunit — Artifact & Spec Format

**Format standard version `openunit-artifact-1`.** This document fixes the
on-disk and on-the-wire byte layout precisely enough for an independent
implementation to reproduce openunit hashes exactly. The authoritative encoder
is `openunit.canonical`; the normative behavior is the text of this document
plus `SPEC.md`. Sections 1–8 are the format; section 9 states conformance and
names the minimal third-party verifier.

## 1. Numbers are strings

Every numeric quantity in a spec and in an artifact is a JSON **string** holding
an exact decimal literal (e.g. `"0.985630795110700089…"`). Numbers are never
JSON numbers and are never built from floats. Implementations must use an exact
decimal type (Python `decimal.Decimal`) with **precision 50** and rounding
**ROUND_HALF_EVEN**, inside a context that does not leak to the caller.

## 2. Canonical encoding (used for all hashing)

A value is canonicalized as UTF-8 bytes of:

```python
json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
```

That is: keys sorted lexicographically, no insignificant whitespace, non-ASCII
emitted literally (not `\uXXXX`). **Hashing always uses this canonical form**,
regardless of how the file is pretty-printed on disk.

Files under `data/` are written pretty-printed (`indent=2`, `ensure_ascii=False`,
trailing newline) for human review. The pretty bytes are **not** what gets
hashed — the canonical bytes are. This is why a vintage can be reformatted for
reading without affecting its `artifact_hash`, and why `make_vintages.py
--verify` compares the pretty bytes it regenerates (to catch accidental edits)
while `verify_artifact` independently recomputes the canonical hashes.

## 3. Hashes

Both hashes are SHA-256 over canonical bytes, rendered lowercase hex with a
`sha256:` prefix:

- `input_digest  = "sha256:" + sha256(canonical(spec)).hexdigest()`
- `artifact_hash = "sha256:" + sha256(canonical(core)).hexdigest()`, where
  `core` is the artifact object **with the `artifact_hash` key removed**.

## 4. Spec object

| key | type | required | notes |
|---|---|---|---|
| `method` | string | yes | `"openunit"` |
| `method_version` | string | no | defaults to `"v0"`; e.g. `"v0.1"`, `"v0.2"` |
| `numeraire` | string | no | defaults to `"USD"` |
| `weight_vintage` | object | yes | must contain `label` (string) and `basis` (string); any other keys are free-form provenance |
| `basket` | array | yes | one or more entries (§5) |
| *(any other keys)* | — | no | permitted; **included in `input_digest`** |

Because every extra key is hashed, descriptive fields such as `provenance`,
`disclaimer`, `note`, `rounding`, or raw `source_*` rates are part of the
spec's identity. Changing any of them changes `input_digest`.

## 5. Basket entry (spec)

| key | type | required | notes |
|---|---|---|---|
| `code` | string | yes | currency / economy code, e.g. `"INR"` |
| `name` | string | no | defaults to `code` |
| `population` | string | yes | exact decimal headcount, `> 0` overall |
| `fx_baseline_usd_per_unit` | string | yes | numeraire per 1 unit at the weight vintage; `> 0` |
| `fx_valuation_usd_per_unit` | string | yes | numeraire per 1 unit on the valuation leg; `> 0` |
| `weight_multiplier` | string | no | defaults to `"1"`; see §2.2 of `SPEC.md` |
| *(any other keys)* | — | no | permitted; hashed as part of the spec |

## 6. Artifact object

Built deterministically from a spec.

| key | type | notes |
|---|---|---|
| `method` | string | `"openunit"` |
| `method_version` | string | copied from the spec (default `"v0"`) |
| `numeraire` | string | copied from the spec (default `"USD"`) |
| `weight_vintage_label` | string | `spec.weight_vintage.label` |
| `weight_basis` | string | `spec.weight_vintage.basis` |
| `baseline_value_usd` | string | `= 1` by construction |
| `value_usd` | string | value of 1 openunit on the valuation leg |
| `basket` | array | per-entry rows (§7) |
| `input_digest` | string | `sha256:` of the spec |
| `artifact_hash` | string | `sha256:` of the artifact minus this field |

The artifact intentionally does **not** echo the spec's free-form provenance;
provenance is bound to the artifact transitively through `input_digest`.

## 7. Basket row (artifact)

Always present:

| key | notes |
|---|---|
| `code` | from the spec entry |
| `name` | from the spec entry (defaults to `code`) |
| `population_share` | pure headcount share `population_i / Σ population` |
| `fixed_amount` | pinned quantity `effective_weight_i / fx_baseline_i` |
| `realized_weight_at_pin` | `= effective_weight_i` (and `= population_share` when no multipliers) |
| `realized_weight_at_valuation` | realized share at the valuation leg |

Present **only when at least one basket entry carries `weight_multiplier`**:

| key | notes |
|---|---|
| `weight_multiplier` | the entry's multiplier (`"1"` if it set one) |
| `effective_weight` | `(population_i · m_i) / Σ (population_j · m_j)` |

This conditional emission is the backward-compatibility rule: with no
multipliers anywhere, the two extra keys are absent and the artifact bytes match
plain openunit v0 exactly.

## 8. Worked reference

The bundled illustrative v0 sample (`sample_input.json`) must always produce:

```
input_digest : sha256:9e5c721b2131fe92059f05d702668d2bcb428afab3a27b1e79da9e578a1ef055
artifact_hash: sha256:433d5e9560f8dcf928c6d2aff9c48ecb9eba558d19fc8eff191056f3f18356bd
```

The real `v0.1-2026-05-15` vintage must produce
`artifact_hash sha256:1e615cf7…9a3a`, and the real-PPP `v0.2-ppp-2026-05-15`
vintage (World Bank `PA.NUS.PPP`, ICP 2024) `sha256:566c95c1…b97a`. Every
bundled vintage is reproduced byte-for-byte by `test_vintages.py`.

## 9. Conformance and the reference verifier

An implementation **conforms** to `openunit-artifact-1` iff, for every spec it
accepts, it produces an artifact identical — byte for byte under the canonical
encoding (§2) — to one built per §§1–8 and `SPEC.md`, and computes the same
`input_digest` and `artifact_hash`. Concretely, a conforming implementation:

1. parses every numeric field as an exact decimal at precision 50,
   `ROUND_HALF_EVEN`, never as a float (§1);
2. hashes only the canonical bytes — keys sorted, `separators=(",", ":")`,
   `ensure_ascii=False`, UTF-8 (§2–3);
3. emits exactly the artifact fields of §6–7, including the conditional
   `weight_multiplier` / `effective_weight` pair **iff** at least one basket
   entry carries a multiplier (the backward-compatibility rule);
4. enforces the input domain of `SPEC.md` ("Input domain"): every `population`
   `≥ 0`, total population `> 0`, total effective weight `> 0`, every FX rate
   `> 0`; otherwise it produces no artifact.

**Minimal third-party verifier.** `verify_independent.py` (bundled) is a second
implementation of this standard written from `SPEC.md` and this document alone —
it never imports `openunit`, `cli`, or `anchor`, and uses only the standard
library. It re-derives every field and both hashes from a spec and compares them
against a published artifact (`python3 verify_independent.py spec.json
artifact.json`, exit 0 iff every field matches). It is both the conformance
oracle for this standard and the tool a third party can run to check a published
value without trusting the openunit engine. `test_independent.py` and
`test_properties.py` cross-validate the engine against it.

**Versioning.** This is `openunit-artifact-1`. A future revision that changes
the byte layout, the field set, the hashing, or the input domain in a
hash-affecting way increments the standard version (`-2`, …); changes that do
not affect any byte (documentation, new optional descriptive spec keys, which
are already hashed transparently per §4) stay within `-1`.
