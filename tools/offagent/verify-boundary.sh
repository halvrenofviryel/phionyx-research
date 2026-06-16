#!/usr/bin/env bash
# Prove the sandbox boundary holds. Run THROUGH the sandbox:
#   tools/offagent/run-agent.sh bash tools/offagent/verify-boundary.sh
# Every check must PASS. Any FAIL means the agent is NOT contained.
REPO="${PHIONYX_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)}"
PH="$HOME/.phionyx"
fail=0
ok()   { echo "PASS: $1"; }
bad()  { echo "FAIL: $1"; fail=1; }

echo "== control-plane paths must be READ-ONLY =="
for p in .claude tools/claude_code_mcp tools/phionyx_mcp_server tools/offagent .git/hooks scripts/active/leak_scan.py; do
  t="$REPO/$p"; [ -d "$t" ] && probe="$t/.probe.$$" || probe="$t"
  if [ -d "$t" ]; then
    if (echo x > "$probe") 2>/dev/null; then bad "$p writable"; rm -f "$probe"; else ok "$p read-only"; fi
  else
    if (echo x >> "$t") 2>/dev/null; then bad "$p writable"; else ok "$p read-only"; fi
  fi
done

echo "== private key must be INVISIBLE =="
if cat "$PH/keys/control_ed25519" >/dev/null 2>&1; then bad "private key readable"; else ok "private key not readable"; fi
if cat "$PH/pub/control_ed25519.pub" >/dev/null 2>&1; then ok "public key readable"; else bad "public key missing"; fi

echo "== repo BODY must stay writable (agent must still work) =="
probe="$REPO/data/.probe.$$"
if (echo x > "$probe") 2>/dev/null; then ok "repo body writable"; rm -f "$probe"; else bad "repo body read-only — agent can't work"; fi

echo "== signed gate must be ARMED =="
[ "${PHIONYX_SIGNED_GATE:-}" = "1" ] && ok "PHIONYX_SIGNED_GATE=1" || bad "PHIONYX_SIGNED_GATE not set"
[ "${PHIONYX_OFFAGENT:-}" = "1" ]    && ok "PHIONYX_OFFAGENT=1"    || bad "PHIONYX_OFFAGENT not set"

echo
[ "$fail" = "0" ] && echo "BOUNDARY HOLDS ✓" || { echo "BOUNDARY BROKEN ✗"; exit 1; }
