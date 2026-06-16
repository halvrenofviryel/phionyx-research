#!/usr/bin/env bash
# OFF-AGENT SIGNER. Run as the KEY HOLDER (you), OUTSIDE the agent sandbox.
# Holds the Ed25519 private key and refreshes the signed control-state from
# telemetry on an interval. This REPLACES the in-agent sign_control_state.py
# PostToolUse hook (which is a no-op when PHIONYX_OFFAGENT=1).
#
# Usage:  tools/offagent/signer-loop.sh            # loop, 20s
#         PHIONYX_SIGNER_INTERVAL=10 tools/offagent/signer-loop.sh
set -euo pipefail
REPO="${PHIONYX_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)}"
PH="$HOME/.phionyx"
export PHIONYX_KEY_DIR="${PHIONYX_KEY_DIR:-$PH/keys}"
export PHIONYX_CONTROL_STATE_FILE="${PHIONYX_CONTROL_STATE_FILE:-$PH/state/control_state.signed.json}"
INTERVAL="${PHIONYX_SIGNER_INTERVAL:-20}"

mkdir -p "$(dirname "$PHIONYX_CONTROL_STATE_FILE")"
[ -f "$PHIONYX_KEY_DIR/control_ed25519" ] || { echo "ERROR: private key $PHIONYX_KEY_DIR/control_ed25519 missing" >&2; exit 1; }

echo "[signer] user=$(whoami) key=$PHIONYX_KEY_DIR state=$PHIONYX_CONTROL_STATE_FILE interval=${INTERVAL}s"
echo "[signer] Ctrl-C to stop."
while true; do
  out="$(python3 "$REPO/tools/claude_code_mcp/control_state.py" --refresh 2>&1 || true)"
  printf '[signer] %s %s\n' "$(date -u +%H:%M:%S)" "$out"
  sleep "$INTERVAL"
done
