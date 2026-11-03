# Reproduce the frozen K1 benchmark

From this experiment directory run:

```sh
python3 -B reproduce.py --out /tmp/acder02-benchmark-replay
```

The output directory must not exist. Requirements: Linux, CPython 3.12 standard library and bubblewrap with user namespaces enabled (measured Python 3.12.3, bwrap 0.9.0). No dependency installation, network, API key, model call or other repository is needed. `python3 -B reproduce.py --check-only` verifies frozen logic and final package hashes without executing comparators.

Both splits run in separate fresh namespaces. Only the Python system runtime, single evaluator source, frozen profile and evidence.json inputs are read-only mounted; an empty output directory is writable. Oracle and latent truth files are not mounted. Scoring happens outside the evaluator only after predictions are produced. Tests include per-scenario determinism and conservation plus target/content, missing receiver/effect, signature-to-execution, no-ACK-to-no-delivery, scope/authority/contradiction and scorer denominator checks.

The runner verifies the complete first-measurement semantic report after removing only machine-specific input file locations. All input hashes, row predictions, oracle states/conditions, latent values, scopes and metric fractions remain in that comparison. Fresh namespace identifiers, temporary paths and wall-clock times may differ; output bytes receive fresh hashes. A failed comparison preserves the new output instead of replacing the original. Outputs are benchmark observations, not a conformance or safety certificate. Full reproduction requires the post-freeze holdout and frozen-results files included in the final package.
