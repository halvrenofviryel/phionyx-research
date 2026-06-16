#!/usr/bin/env bash
# update_snapshot.sh — refresh the case-study snapshots from a working
# Phionyx development clone (the private development monorepo). Reads the
# audit + scenario scripts in the parent repo and copies their latest
# outputs into snapshots/.
#
# Usage:
#   PHIONYX_PRIVATE_ROOT=/path/to/monorepo ./update_snapshot.sh
#
# Pre-condition: $PHIONYX_PRIVATE_ROOT must be a checked-out Phionyx
# development monorepo with `data/mcp_telemetry/` and the audit scripts
# present. The script will refuse to run otherwise.

set -euo pipefail

PRIVATE_ROOT="${PHIONYX_PRIVATE_ROOT:-}"
if [[ -z "$PRIVATE_ROOT" ]]; then
  echo "error: PHIONYX_PRIVATE_ROOT must point at a Phionyx dev monorepo" >&2
  exit 1
fi

if [[ ! -d "$PRIVATE_ROOT/data/mcp_telemetry" ]]; then
  echo "error: $PRIVATE_ROOT does not look like a Phionyx dev root" >&2
  exit 2
fi

CASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SNAPS_DIR="$CASE_DIR/snapshots"

cd "$PRIVATE_ROOT"
python3 scripts/active/runtime_evidence_self_audit.py --days 30 \
  --out "/tmp/audit_$(date +%Y-%m-%d).md"
python3 scripts/active/runtime_evidence_test_scenarios.py \
  --out "/tmp/scenarios_$(date +%Y-%m-%d).md"

DATE=$(date +%Y-%m-%d)
cp "/tmp/audit_${DATE}.md" "$SNAPS_DIR/audit_${DATE}.md"
cp "/tmp/scenarios_${DATE}.md" "$SNAPS_DIR/scenarios_${DATE}.md"

# Optional: regenerate the coverage figure. Set PHIONYX_FIGURE_DIR to the
# directory in your dev clone holding render_figures.py + the rendered PNG.
if [[ -n "${PHIONYX_FIGURE_DIR:-}" ]] && command -v python3 >/dev/null && python3 -c "import matplotlib" 2>/dev/null; then
  python3 "$PHIONYX_FIGURE_DIR/render_figures.py" --figure 4
  cp "$PHIONYX_FIGURE_DIR/fig4_coverage_timeline.png" \
    "$CASE_DIR/figures/coverage_timeline.png"
fi

echo "snapshot refreshed: snapshots/audit_${DATE}.md + scenarios_${DATE}.md"
echo
echo "next step: review the diff in this case-study directory, then:"
echo "  git add -A case-studies/agentic-development-2026-05/"
echo "  git commit -m \"chore(case-study): refresh snapshot ${DATE}\""
echo "  git push origin main"
