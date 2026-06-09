#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
openunit anchoring -- commit an artifact_hash to a tamper-evident record.

Scope (deliberately small and offline):
  - The *core* anchoring is a deterministic commitment over an artifact_hash,
    optionally chained onto a previous anchor to form an append-only log
    (a head-hash / hash-chain notarization, in the spirit of OpenTimestamps).
  - It performs NO network calls and uses NO secret keys: producing a public,
    independently-checkable timestamp (a blockchain transaction or an
    OpenTimestamps `.ots` proof) is an *external* step, documented in
    docs/ANCHORING.md. The optional `external_proof` field carries that proof
    and is intentionally NOT part of the commitment, so attaching it later
    does not change any hash.

Why anchor at all? openunit's value is reproducibility, not authority. Anchoring
lets a publisher say "this exact artifact existed by this point and has not been
silently revised", which is what a measuring stick needs -- nothing more.

Determinism: stdlib only; no wall clock; SHA-256 over canonical JSON.
"""

import hashlib

from openunit import canonical  # reuse the engine's canonical encoder

ANCHOR_VERSION = "openunit-anchor-1"


def _sha256(obj):
    return "sha256:" + hashlib.sha256(canonical(obj)).hexdigest()


def make_anchor(artifact, prev_anchor=None, label=None):
    """Create an anchor record committing to `artifact`'s artifact_hash.

    If `prev_anchor` is given, the new record chains onto it (sequence + 1 and
    prev_commitment = prev_anchor['commitment']); otherwise it is a genesis
    anchor (sequence 0, prev_commitment None).
    """
    artifact_hash = artifact["artifact_hash"]
    if prev_anchor is None:
        sequence = 0
        prev_commitment = None
    else:
        sequence = int(prev_anchor["sequence"]) + 1
        prev_commitment = prev_anchor["commitment"]

    core = {
        "version": ANCHOR_VERSION,
        "artifact_hash": artifact_hash,
        "sequence": sequence,
        "prev_commitment": prev_commitment,
        "label": label,
    }
    record = dict(core)
    record["commitment"] = _sha256(core)
    # Slot for an external public timestamp (e.g. an OpenTimestamps .ots blob or
    # a chain txid). Not covered by the commitment, so it can be filled in later.
    record["external_proof"] = None
    return record


def verify_anchor(anchor, artifact, prev_anchor=None, explain=False):
    """True iff the anchor commits to this artifact and chains correctly."""
    reasons = []

    if anchor.get("artifact_hash") != artifact.get("artifact_hash"):
        reasons.append("anchor artifact_hash does not match the artifact")

    seq = anchor.get("sequence")
    prev_c = anchor.get("prev_commitment")
    if prev_anchor is None:
        if seq != 0:
            reasons.append("genesis anchor must have sequence 0")
        if prev_c is not None:
            reasons.append("genesis anchor must have prev_commitment = null")
    else:
        if seq != int(prev_anchor["sequence"]) + 1:
            reasons.append("sequence is not previous + 1")
        if prev_c != prev_anchor.get("commitment"):
            reasons.append("prev_commitment does not match previous anchor")

    core = {
        "version": anchor.get("version"),
        "artifact_hash": anchor.get("artifact_hash"),
        "sequence": seq,
        "prev_commitment": prev_c,
        "label": anchor.get("label"),
    }
    if _sha256(core) != anchor.get("commitment"):
        reasons.append("commitment does not match the anchored content")

    ok = not reasons
    if explain and not ok:
        for r in reasons:
            print("  - " + r)
    return ok
