#!/usr/bin/env bash
# Launch Claude Code inside a bubblewrap MOUNT-NAMESPACE SANDBOX where the
# control plane is READ-ONLY and the private key is INVISIBLE. The agent keeps
# the full host environment (node, python, OAuth, MCP servers) — only the
# governance surface is locked.
#
# WHY a sandbox and not filesystem perms: the repo lives on an NTFS mount
# (ntfs-3g) that forces every file to root:root 777 and ignores chown/chmod.
# A read-only bind mount is enforced by the kernel VFS regardless of the backing
# filesystem — so it holds where chmod cannot. (See tools/offagent/README.md.)
#
# PREREQUISITE: unprivileged user namespaces must be allowed for bwrap. On
# Ubuntu 24.04 (kernel.apparmor_restrict_unprivileged_userns=1) install the
# scoped profile first:
#   sudo cp tools/offagent/apparmor-bwrap /etc/apparmor.d/bwrap
#   sudo apparmor_parser -r /etc/apparmor.d/bwrap
#
# Usage:  tools/offagent/run-agent.sh                 # launch claude (sandboxed)
#         tools/offagent/run-agent.sh bash            # shell in the sandbox (debug)
#         tools/offagent/run-agent.sh bash tools/offagent/verify-boundary.sh
set -euo pipefail
REPO="${PHIONYX_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)}"
PH="$HOME/.phionyx"
PUB="$PH/pub"
STATE="$PH/state"
CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.local/bin/claude}"

[ -f "$PUB/control_ed25519.pub" ] || { echo "ERROR: $PUB/control_ed25519.pub missing — run tools/offagent/setup.sh first" >&2; exit 1; }

# Control-plane paths: READ-ONLY in the sandbox. The agent can execute the hooks
# and read the config, but cannot rewrite what governs it.
RO_PATHS=(
  "$REPO/.claude"
  "$REPO/tools/claude_code_mcp"
  "$REPO/tools/phionyx_mcp_server"
  "$REPO/tools/offagent"
  "$REPO/.git/hooks"
  "$REPO/scripts/active/leak_scan.py"
)

args=( --bind / / --dev /dev --proc /proc --tmpfs "$PH/keys" )   # mirror host rw; real /dev+/proc; MASK private key dir
for p in "${RO_PATHS[@]}"; do
  [ -e "$p" ] && args+=( --ro-bind "$p" "$p" )
done
args+=( --ro-bind "$PUB" "$PUB" --ro-bind "$STATE" "$STATE" )
args+=(
  --setenv PHIONYX_SIGNED_GATE 1
  --setenv PHIONYX_OFFAGENT 1
  --setenv PHIONYX_KEY_DIR "$PUB"
  --setenv PHIONYX_CONTROL_STATE_FILE "$STATE/control_state.signed.json"
  --chdir "$REPO"
)

if [ "$#" -eq 0 ]; then set -- "$CLAUDE_BIN"; fi
exec bwrap "${args[@]}" "$@"
