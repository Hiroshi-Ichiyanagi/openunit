# openunit — Anchoring

Anchoring lets a publisher make a small, tamper-evident claim:

> *this exact artifact existed by this point in time, and has not been silently
> revised since.*

That is all a measuring stick needs. openunit's value is **reproducibility, not
authority**, so anchoring deliberately does the minimum and stays auditable.

## What the core does (offline, keyless, deterministic)

`anchor.py` (and `openunit anchor` / `openunit verify-anchor`) builds an
**anchor record**: a deterministic SHA-256 commitment over an `artifact_hash`,
optionally chained onto a previous anchor to form an append-only log.

```
core = {
  "version":         "openunit-anchor-1",
  "artifact_hash":   "<the artifact's sha256:… hash>",
  "sequence":        <0 for genesis, prev.sequence + 1 otherwise>,
  "prev_commitment": <null for genesis, prev.commitment otherwise>,
  "label":           <optional human string, or null>
}
commitment = "sha256:" + sha256(canonical(core)).hexdigest()
```

The record stored on disk is `core` plus `commitment` plus an `external_proof`
slot (see below). Like the engine, the anchor uses the standard library only,
reads no wall clock, and uses no secret keys. The commitment is fully
recomputable by anyone holding the record.

### Chaining

Anchors chain into an append-only log: each non-genesis record sets
`sequence = previous + 1` and `prev_commitment = previous.commitment`. Breaking
the chain — reordering, dropping, or altering a record — fails verification,
because the commitments no longer line up.

```sh
openunit anchor artifact.json -o anchor-000.json --label "v0.1 published"
openunit anchor next.json     -o anchor-001.json --prev anchor-000.json
openunit verify-anchor anchor-001.json next.json --prev anchor-000.json
```

`verify_anchor` checks that the record commits to *this* artifact, that the
sequence and `prev_commitment` are consistent with the supplied previous anchor
(or that a genesis record has `sequence 0` / `prev_commitment null`), and that
the stored `commitment` matches a freshly recomputed one.

## What the core does *not* do (and why)

A purely local hash-chain proves **integrity and order**, not **time**: on its
own it cannot stop someone from recreating the whole chain after the fact. To
get an independently checkable *timestamp*, attach an external proof:

- **OpenTimestamps.** Timestamp the `commitment` (or `artifact_hash`) and store
  the resulting `.ots` proof, which is later verifiable against the Bitcoin
  blockchain. See <https://opentimestamps.org/>.
- **A blockchain transaction.** Publish the `commitment` in a transaction (e.g.
  an `OP_RETURN`) and store the txid and network.
- **A trusted timestamping authority (RFC 3161).** Store the returned token.

The proof goes in the record's `external_proof` field:

```json
{
  "version": "openunit-anchor-1",
  "artifact_hash": "sha256:1e615cf7…9a3a",
  "sequence": 0,
  "prev_commitment": null,
  "label": "v0.1 published",
  "commitment": "sha256:…",
  "external_proof": { "type": "ots", "blob": "…base64…" }
}
```

**`external_proof` is intentionally outside the commitment.** It is not part of
`core`, so attaching, replacing, or removing it never changes `commitment` and
never breaks `verify_anchor`. This lets you anchor immediately and obtain the
slower public timestamp afterwards. Verifying the external proof itself is done
with the corresponding external tool (e.g. the OpenTimestamps client), not by
openunit.

## Threat model in one line

- *Silent revision of a published value* → detected: the artifact no longer
  matches the committed `artifact_hash`.
- *Reordering or deletion within a published log* → detected: the chain links
  break.
- *Backdating* → not addressed by the offline core; addressed by attaching an
  `external_proof` from a public timestamp.

## Third-party timestamp (OpenTimestamps)

The two shipped vintages carry an OpenTimestamps proof committing each
`artifact.json` to the Bitcoin blockchain, so a third party can confirm the
artifact existed by a point in time without trusting this repository. The proofs
are `data/v0.1-2026-05-15/artifact.json.ots` and
`data/v0.2-ppp-2026-05-15/artifact.json.ots`; OpenTimestamps commits to the
**bytes of the `artifact.json` file** (not openunit's internal `artifact_hash`,
which is a separate, in-document hash), so verification needs the exact file the
proof was made from. To check one — using only the standard OpenTimestamps
client, never openunit — run `ots verify data/v0.1-2026-05-15/artifact.json.ots`
(it locates `data/v0.1-2026-05-15/artifact.json` automatically). A proof is
created as a *calendar commitment* and is initially **pending** Bitcoin
confirmation; once the calendars fold it into a block (typically hours to a day
later), `ots upgrade data/v0.1-2026-05-15/artifact.json.ots` rewrites the `.ots`
with the Bitcoin attestation and `ots verify` then reports the confirming block
height and time. The `.ots` files live outside every openunit hash, so adding or
upgrading them changes no `artifact_hash` and no `input_digest`.
