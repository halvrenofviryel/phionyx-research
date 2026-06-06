# Phionyx Core SDK — v0.8.0 Release Notes

- **Date:** 2026-06-06
- **Type:** Minor release — Production Hardening (schema-freeze **candidate**)
- **Package:** `phionyx-core` on PyPI · Python 3.10–3.13

---

## What is Phionyx?

`phionyx-core` is a deterministic, auditable AI cognition runtime. It treats LLM output as a
noisy sensor measurement — not as truth — and runs every turn through a fixed, reproducible
pipeline that produces a signed, replayable evidence record. Given identical inputs, the
cognitive path is reproducible.

## What's new in v0.8.0

v0.8.0 hardens the existing runtime rather than adding product features. Five things land:

### Hardening
- **Real 8-axiom CI gate** — the Echoism axiom suite now asserts genuine invariants in CI,
  replacing a previously always-passing aggregator. A green build now means something.
- **Adversarial corpus + confusion matrix** — a 30-safe / 30-unsafe input regression set with
  a published baseline recall, run in CI.
- **10K-envelope performance benchmark + latency gate** — sub-millisecond per-envelope
  verification, wired as a CI regression gate so latency cannot silently drift.

### Contracts
- **`contracts/interlink/`** — the cross-runtime interchange envelope now lives inside the
  package (additive).
- **`contracts/v4/claim.py`** — a typed `Claim` lifecycle contract: a `claim_id` is tracked
  from creation → gate decision → signed record → observed outcome, with an
  `is_lifecycle_complete()` predicate. Realized through the existing pipeline; no new blocks.

### Cryptographic consistency
- **Signed-chain canonicalization → RFC 8785 (JCS)** — the signed audit chain now
  canonicalizes byte-identically with the evidence-export path, removing float and non-ASCII
  divergence. **Breaking:** chains persisted by earlier versions no longer verify; new chains
  are JCS-consistent. The frozen hash-record domain is unchanged.

### Quality & privacy
- **Type-modernization sweep** — PEP 585/604 generics across the source; `ruff`- and
  `mypy`-clean on 3.10–3.13. No behavioral change.
- **Privacy rebuild** — genericized example/keyword data in the context and narrative modules
  to remove maintainer-personal and domain-specific literals from the published package. No
  behavioral change.

## Not a schema freeze

v0.8.0 is a schema-freeze **candidate**, not a freeze. The v1.0 freeze is a separate
milestone. The version axes — product release, RGE wire schema, V4 contract suite, pipeline
contract, and the AIREP protocol — are intentionally independent and each follow their own
bump rules. The docs site, companion-package republish, and external audit are independent
workstreams that do not gate this package release.

## Install

```bash
pip install --upgrade phionyx-core==0.8.0
python -c "import phionyx_core; print(phionyx_core.__version__)"  # 0.8.0
```

## License

AGPL-3.0. See [`LICENSE`](../../LICENSE). Patent rights retained by Phionyx Research.

## Links

- PyPI: https://pypi.org/project/phionyx-core/
- Changelog: [`CHANGELOG.md`](../../CHANGELOG.md)
- Website: https://phionyx.ai
