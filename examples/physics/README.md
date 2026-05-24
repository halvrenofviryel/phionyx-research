# `examples/physics/`

Worked-example traces for the physics layer of phionyx-core.

## Files

- **`npc_drift_demo.py`** — Reference trace of the NPC drift detection
  pattern: same NPC profile, same scenario, four turns. Drift is detected
  on the cognitive channel one turn before the visible character break.
  The script is the source of the interactive stepper on the
  [Narrative Coherence](https://phionyx.ai/narrative-coherence) page.

## Status — runnable in v0.6.0+; source-inspectable today

> **PyPI `phionyx-core` v0.5.0 does NOT yet expose every classifier
> function this demo imports.** Specifically, `classify_resonance_normalized`
> in `phionyx_core.physics.formulas` is part of the v0.6.0 surface, not
> v0.5.0. Running these scripts against the public v0.5.0 wheel will
> raise `ImportError`.

This is intentional. The classifier surface is being reviewed before
the v0.6.0 release; the source is published here so reviewers can inspect
the logic, audit the inputs and thresholds, and follow the imports — but
executing the script end-to-end is gated to v0.6.0.

Until v0.6.0 releases, the **byte-exact JSON envelope** of the reference
run is the reviewer-verifiable artefact:

- Web inspection: [phionyx.ai/narrative-coherence](https://phionyx.ai/narrative-coherence)
  (interactive stepper renders the envelope turn-by-turn)
- Direct download: [phionyx.ai/demos/npc-drift.json](https://phionyx.ai/demos/npc-drift.json)

After v0.6.0, `pip install phionyx-core>=0.6.0` and the run command
documented inside `npc_drift_demo.py` will produce a JSON sidecar
byte-identical to the committed envelope.

## What the script imports (for source review)

```
from phionyx_core.physics.constants  import CONTEXT_WEIGHTS
from phionyx_core.physics.formulas   import calculate_phi_v2_1,
                                            classify_resonance_normalized
```

Both modules are already visible in this repository under
[`phionyx_core/physics/`](../../phionyx_core/physics/). Reviewers can
follow the imports and read the formulas + constants used to score each
turn directly from this tree, even before the classifier surface is
released on PyPI.

## License

Same as the parent repository — AGPL-3.0 with the commercial dual-license
option documented in [`LICENSE_STRATEGY.md`](../../LICENSE_STRATEGY.md).
