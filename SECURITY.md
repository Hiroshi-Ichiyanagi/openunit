# Security Policy

## Scope

openunit is a *measuring stick*: a deterministic library, CLI, and set of data
vintages. It holds no funds, manages no keys, runs no service, and performs no
network or filesystem I/O in its engine. There is no wallet, account, or
custody surface to attack. Its security properties are therefore narrow and
specific:

- **Reproducibility.** The same spec must always yield the same artifact and the
  same hashes, on any machine, at any time.
- **Integrity / tamper-evidence.** A published artifact that has been altered
  must fail `verify_artifact`; an altered or reordered anchor log must fail
  `verify_anchor`.

## What counts as a vulnerability

- A way to make `build_artifact` non-deterministic (output depends on time,
  platform, locale, randomness, decimal-context leakage, hash-iteration order,
  etc.).
- A way to make `verify_artifact` return `True` for an artifact that does not
  actually reproduce from its spec, or for a tampered artifact.
- A way to make `verify_anchor` accept a record that does not commit to the
  artifact, or that breaks the chain rules.
- A documentation or data error that would cause a vintage to be treated as
  authoritative when its inputs are illustrative.

## What is out of scope

- The trustworthiness of the *external* inputs themselves (UN/ECB/World Bank
  figures); openunit only guarantees faithful, exact computation over the inputs
  recorded in each vintage's `SOURCES.md`.
- Backdating prevention from the offline anchor core alone — that requires an
  external public timestamp (see `docs/ANCHORING.md`).

## Reporting

Please report suspected issues privately to the maintainers (e.g. via a GitHub
security advisory on the repository) rather than opening a public issue, and
allow reasonable time to respond before disclosure. A minimal reproduction —
ideally a spec and the unexpected artifact — is the most useful thing you can
include.
