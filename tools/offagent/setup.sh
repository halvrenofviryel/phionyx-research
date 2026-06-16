#!/usr/bin/env bash
# Off-agent control-plane setup (key-custody side). Run ONCE as the key holder
# (you, the normal account). Creates:
#   ~/.phionyx/pub/    public key ONLY — mounted read-only into the agent sandbox
#   ~/.phionyx/state/  signed state file — its own dir so a dir-bind sees the
#                      signer's atomic rename-replace (a file-bind would pin the
#                      old inode and the agent would never see refreshes).
# The PRIVATE key in ~/.phionyx/keys is NEVER copied and NEVER mounted in.
set -euo pipefail
PH="$HOME/.phionyx"
KEYS="$PH/keys"

[ -f "$KEYS/control_ed25519.pub" ] || { echo "ERROR: $KEYS/control_ed25519.pub missing — run provision_offagent_control.sh first" >&2; exit 1; }

mkdir -p "$PH/pub" "$PH/state"
chmod 755 "$PH/pub" "$PH/state"

cp "$KEYS/control_ed25519.pub" "$PH/pub/control_ed25519.pub"
chmod 644 "$PH/pub/control_ed25519.pub"

# relocate any legacy signed state into state/
if [ -f "$PH/control_state.signed.json" ] && [ ! -f "$PH/state/control_state.signed.json" ]; then
  mv -f "$PH/control_state.signed.json" "$PH/state/control_state.signed.json"
fi
touch "$PH/state/control_state.signed.json"
chmod 644 "$PH/state/control_state.signed.json"

echo "OK:"
echo "  pub  : $PH/pub/control_ed25519.pub  (public key only)"
echo "  state: $PH/state/control_state.signed.json"
echo "  keys : $KEYS  (private key — NOT copied, masked in sandbox)"
