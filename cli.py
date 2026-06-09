#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
openunit command-line interface.

    openunit build  <spec.json> [-o artifact.json]
    openunit verify <artifact.json> <spec.json>
    openunit show   <artifact.json>
    openunit anchor <artifact.json> [-o anchor.json] [--prev prev.json] [--label L]
    openunit verify-anchor <anchor.json> <artifact.json> [--prev prev.json]

Exit code 0 on success, 1 on any verification failure or error. The CLI is a
thin wrapper over the engine (openunit.py) and the anchoring helper (anchor.py);
all determinism guarantees live there.
"""

import sys
import json
import argparse
from decimal import Decimal

import openunit
import anchor as anchor_mod


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _dump(obj, path=None):
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


def cmd_build(args):
    spec = _load(args.spec)
    art = openunit.build_artifact(spec)
    if not openunit.verify_artifact(art, spec):
        print("ERROR: built artifact failed self-verification", file=sys.stderr)
        return 1
    _dump(art, args.output)
    if args.output:
        v = Decimal(art["value_usd"]).quantize(Decimal("0.000001"))
        print("built %s  ->  1 openunit = %s %s"
              % (args.output, v, art["numeraire"]))
        print("artifact_hash: %s" % art["artifact_hash"])
    return 0


def cmd_verify(args):
    art = _load(args.artifact)
    spec = _load(args.spec)
    ok = openunit.verify_artifact(art, spec, explain=True)
    print("VERIFIED" if ok else "FAILED")
    return 0 if ok else 1


def cmd_show(args):
    art = _load(args.artifact)
    v = Decimal(art["value_usd"]).quantize(Decimal("0.000001"))
    print("method        : %s %s" % (art["method"], art["method_version"]))
    print("1 openunit    : %s %s" % (v, art["numeraire"]))
    print("weight basis  : %s" % art["weight_basis"])
    print("vintage       : %s" % art["weight_vintage_label"])
    print("input_digest  : %s" % art["input_digest"])
    print("artifact_hash : %s" % art["artifact_hash"])
    return 0


def cmd_anchor(args):
    art = _load(args.artifact)
    prev = _load(args.prev) if args.prev else None
    rec = anchor_mod.make_anchor(art, prev_anchor=prev, label=args.label)
    _dump(rec, args.output)
    if args.output:
        print("anchored -> %s" % args.output)
        print("sequence   : %d" % rec["sequence"])
        print("commitment : %s" % rec["commitment"])
    return 0


def cmd_verify_anchor(args):
    rec = _load(args.anchor)
    art = _load(args.artifact)
    prev = _load(args.prev) if args.prev else None
    ok = anchor_mod.verify_anchor(rec, art, prev_anchor=prev, explain=True)
    print("ANCHOR OK" if ok else "ANCHOR FAILED")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="openunit", description="openunit CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="build an artifact from a spec")
    b.add_argument("spec")
    b.add_argument("-o", "--output")
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("verify", help="verify an artifact against its spec")
    v.add_argument("artifact")
    v.add_argument("spec")
    v.set_defaults(func=cmd_verify)

    s = sub.add_parser("show", help="print a one-screen summary of an artifact")
    s.add_argument("artifact")
    s.set_defaults(func=cmd_show)

    a = sub.add_parser("anchor", help="make a tamper-evident anchor record")
    a.add_argument("artifact")
    a.add_argument("-o", "--output")
    a.add_argument("--prev", help="previous anchor record to chain onto")
    a.add_argument("--label", help="optional human label")
    a.set_defaults(func=cmd_anchor)

    va = sub.add_parser("verify-anchor", help="verify an anchor record")
    va.add_argument("anchor")
    va.add_argument("artifact")
    va.add_argument("--prev", help="previous anchor record in the chain")
    va.set_defaults(func=cmd_verify_anchor)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
