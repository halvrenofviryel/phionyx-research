# OpenTelemetry GenAI Semantic Conventions — Phionyx bump policy

**Status:** Active
**Owner:** `phionyx_core/telemetry/`
**Reviewed:** 2026-05-19

---

## Why this document exists

The [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) are at **Development** status as of v1.36.0 (verified 2026-05-19). The spec is actively being shaped by the OTel GenAI SIG and vendor working groups; attribute names, value cardinalities, and event/metric shapes can change between minor versions.

Phionyx ships an OTel envelope exporter (`phionyx_core/telemetry/otel_export.py`). That exporter emits spans whose attribute names follow the GenAI conventions. **Users who enable the exporter today should not be silently broken by a future spec revision.** This document is the contract.

---

## What we promise

1. **Every emitted span attribute is pinned to a specific spec version.** The mapping lives in `phionyx_core/telemetry/otel_semantic_v<MAJ>_<MIN>_<PATCH>.py`. The default pin is exported as `phionyx_core.telemetry.DEFAULT_SEMANTIC_VERSION`.

2. **Users can pin explicitly.** Setting `PHIONYX_OTEL_SEMANTIC_VERSION=v1.36.0` (or any other supported value) overrides the package default. The exporter raises `ValueError` at first call when an unsupported version is requested — never silently downgrade.

3. **Two-version compatibility window.** When we change the default pin in a Phionyx minor release, the previous pin remains importable for at least two more Phionyx minor releases. Example: if v0.5.0 bumps default from `v1.36.0` to `v1.37.0`, then `PHIONYX_OTEL_SEMANTIC_VERSION=v1.36.0` continues to work through v0.7.x.

4. **Breaking spec changes generate a CHANGELOG note.** Any spec change that renames, removes, or restructures an attribute we currently emit is called out in `CHANGELOG.md` under a `### OpenTelemetry conventions` subhead.

5. **The exporter is opt-in.** `PHIONYX_OTEL_EXPORT_ENVELOPES=true` is required to emit envelope spans. Operators who haven't opted in are unaffected by any of the above.

---

## When we bump the default pin

A bump from `v1.X.0` to `v1.Y.0` in the Phionyx default requires:

| Condition | How we verify |
|---|---|
| The new version has been published and marked at least **Development** (no Experimental-only renames) | Read the spec page; check the version stamp |
| Every attribute Phionyx currently emits exists in the new version (renames are explicitly mapped, not silently dropped) | Diff `otel_semantic_v<old>` against the new spec |
| Two backend vendors have shipped support for the new version | Check Datadog / Langfuse / Honeycomb / New Relic / Tempo release notes |
| A Phionyx integration test runs against both versions | `tests/integration/test_otel_envelope_export.py` parametrised over the version |
| `CHANGELOG.md` has a clear migration note | Reviewer pass before tag |

We **do not** bump on every spec minor. Stability for users matters more than chasing the latest names.

---

## When the spec breaks Phionyx attributes

If the OTel spec deprecates or restructures an attribute Phionyx currently emits, the response sequence is:

1. **Same Phionyx minor release:** add a new semantic module (`otel_semantic_v<MAJ>_<MIN>_<PATCH>.py`) that captures the new names. The new module is **not** the default yet.
2. **Next Phionyx minor release:** make the new module available via `PHIONYX_OTEL_SEMANTIC_VERSION`. Old module remains the default.
3. **Two minors after the spec break:** bump the default. Old module remains importable but marked `# DEPRECATED: pinned to <spec-version>; will be removed in v<next-minor>` at the top of the file.
4. **One minor after the deprecation:** remove the old module. Users on the old pin will fail loudly at startup, not silently.

---

## Phionyx-specific (`phionyx.*`) attributes

Phionyx-specific attributes live in the `phionyx.*` namespace and are **not** governed by the OTel spec. They evolve under Phionyx's own SemVer:

- Adding a new `phionyx.*` attribute → minor bump
- Renaming or removing a `phionyx.*` attribute → major bump
- Changing the value semantics (e.g. from string to enum) → major bump

The semantic-version module file names refer to the **OTel** pinned spec version; the `phionyx.*` attribute list inside each module evolves with Phionyx's version, captured in `CHANGELOG.md`.

---

## Concrete history

| Phionyx version | OTel default pin | Notes |
|---|---|---|
| 0.4.0 | `v1.36.0` | Initial release of the envelope exporter (F2). Status: Development. |

(Append rows as default pins bump.)

---

## Why version pinning beats "follow latest"

If we emitted attribute names from a moving spec, every Phionyx user enabling the exporter would inherit the OTel SIG's iteration risk. A vendor backend tuned to attribute `gen_ai.request.model` would silently lose visibility when that name became `gen_ai.model.request`. Pinning costs a small amount of code maintenance on our side; "follow latest" costs every downstream user their dashboards.

The exporter is opt-in for the same reason: operators who don't want to track the spec's evolution don't have to.

---

## See also

- `phionyx_core/telemetry/otel_export.py` — exporter implementation
- `phionyx_core/telemetry/otel_semantic_v1_36_0.py` — current pinned attribute table
- `tests/integration/test_otel_envelope_export.py` — emission test
- `tests/unit/core/telemetry/test_otel_export.py` — mapping unit tests
- OTel GenAI spec: https://opentelemetry.io/docs/specs/semconv/gen-ai/
