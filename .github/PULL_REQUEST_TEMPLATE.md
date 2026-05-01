<!--
Thanks for the PR. The shape below mirrors the questions a reviewer
would ask anyway; pre-answering them speeds review.

For very small PRs (typo, comment, version bump), the structure is
optional — a one-line summary is fine.
-->

## Summary

<!-- One or two sentences: what changes, why now. -->

## Layer + determinism

<!--
Which layer does this touch? (phionyx_core kernel / phionyx_core.ports /
adapter / examples / docs / CI / packaging)

If it adds a `PipelineBlock`, declare its `determinism` class
(`strict` / `seeded` / `noisy_sensor`) and why.
-->

## How to verify

<!--
Concrete steps. Prefer:

  pytest tests/core -q
  ruff check phionyx_core
  python -m build && twine check dist/*

over "I tested it locally". CI runs the same checks; if you can paste
the local output it shortens the loop.
-->

## Risk

<!--
- Public API surface changed? List the symbols.
- Determinism contract: any block now `noisy_sensor` that wasn't?
- Audit-record schema touched? (compute_hash() value should not change
  unless intentional — bump schema version if it does.)
- Required dependency added? Justify; we keep the base set small so
  `pip install phionyx-core` stays light.
-->

## Linked issues

<!-- e.g. closes #123, refs #45 -->
