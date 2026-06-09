#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_anchor.py -- anchoring commitment, hash-chaining, tamper detection.

Standalone (`python3 test_anchor.py`) and pytest compatible.
"""

import copy
import anchor as A


ART1 = {"artifact_hash": "sha256:" + "a" * 64}
ART2 = {"artifact_hash": "sha256:" + "b" * 64}


def test_genesis_verifies():
    rec = A.make_anchor(ART1, label="first")
    assert rec["sequence"] == 0
    assert rec["prev_commitment"] is None
    assert A.verify_anchor(rec, ART1)


def test_chain_verifies():
    g = A.make_anchor(ART1)
    n = A.make_anchor(ART2, prev_anchor=g, label="second")
    assert n["sequence"] == 1
    assert n["prev_commitment"] == g["commitment"]
    assert A.verify_anchor(n, ART2, prev_anchor=g)


def test_wrong_artifact_fails():
    rec = A.make_anchor(ART1)
    assert not A.verify_anchor(rec, ART2)


def test_tampered_commitment_fails():
    rec = A.make_anchor(ART1)
    bad = copy.deepcopy(rec)
    bad["artifact_hash"] = ART2["artifact_hash"]  # change content, keep commitment
    assert not A.verify_anchor(bad, ART2)


def test_broken_chain_fails():
    g = A.make_anchor(ART1)
    n = A.make_anchor(ART2, prev_anchor=g)
    broken = copy.deepcopy(n)
    broken["prev_commitment"] = "sha256:" + "c" * 64
    assert not A.verify_anchor(broken, ART2, prev_anchor=g)


def test_external_proof_does_not_change_commitment():
    rec = A.make_anchor(ART1)
    c0 = rec["commitment"]
    rec["external_proof"] = {"type": "ots", "blob": "deadbeef"}
    # commitment must still verify after attaching a proof
    assert A.verify_anchor(rec, ART1)
    assert rec["commitment"] == c0


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS  " + t.__name__)
        except AssertionError as exc:
            failed += 1
            print("FAIL  %s: %s" % (t.__name__, exc))
    print("-" * 50)
    print("%d/%d PASS" % (len(tests) - failed, len(tests)))
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(1 if _run() else 0)
