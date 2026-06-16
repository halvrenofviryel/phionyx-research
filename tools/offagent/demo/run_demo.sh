#!/usr/bin/env bash
# Phionyx control-hardening demo (Phase 5). Shows the SAME seven adversarial attempts
# under three postures, side by side:
#
#   1. UNGOVERNED  — no control plane: every exploit succeeds.
#   2. GOVERNED (direct launch) — Phionyx hooks active, but the workspace is not
#      capability-bounded: fail-closed gates HOLD the gated actions; documented gaps remain.
#   3. GOVERNED + SANDBOXED (run-agent.sh) — same hooks INSIDE the bwrap capability
#      sandbox: the control plane is a kernel read-only bind, so the bash-write exploit
#      that slipped through on a direct launch now fails (EROFS).
#
# It performs NO destructive action and makes NO external effect — each "exploit" is a
# crafted tool-call payload fed to the real gate, and we record the gate's verdict.
#
# Honest scope: this is COOPERATIVE-GRADE governance with a capability boundary, not
# "containment". Key custody is real only under run-agent.sh; obfuscated commands and
# natural-language false claims are documented permanent limits. See README.md.
#
# Usage:  tools/offagent/demo/run_demo.sh            # baseline + direct (no sudo needed)
#         tools/offagent/demo/run_demo.sh --sandbox  # also runs the sandboxed posture
set -euo pipefail
REPO="${PHIONYX_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../../.." && pwd)}"
EVAL="$REPO/tools/offagent/control_eval.py"
OUT="$REPO/tools/offagent/demo/evidence"
mkdir -p "$OUT"

bar() { printf '%.0s=' {1..78}; echo; }

bar
echo "PHIONYX CONTROL-HARDENING DEMO — same exploits, three postures"
bar

echo; echo ">>> POSTURE 1 — UNGOVERNED (no control plane)"
python3 "$EVAL" --baseline | tail -n +1
python3 "$EVAL" --baseline --json > "$OUT/1_ungoverned.json"

echo; echo ">>> POSTURE 2 — GOVERNED (direct / unsandboxed launch)"
python3 "$EVAL"
python3 "$EVAL" --json > "$OUT/2_governed_direct.json"

if [ "${1:-}" = "--sandbox" ]; then
  echo; echo ">>> POSTURE 3 — GOVERNED + SANDBOXED (run-agent.sh)"
  "$REPO/tools/offagent/run-agent.sh" bash -c "python3 '$EVAL'"
  "$REPO/tools/offagent/run-agent.sh" bash -c "python3 '$EVAL' --json" > "$OUT/3_governed_sandboxed.json"
else
  echo; echo "(skip POSTURE 3 — re-run with --sandbox to show the EROFS flip; needs the bwrap prereq)"
fi

echo; bar
echo "Evidence JSON written to: $OUT/"
echo "Read tools/offagent/demo/README.md for the narrative + honest scope."
bar
