"""Verify PRE Optimization Tracker — auto-generate summary from source of truth.

Reads surfaces.yaml (parameter definitions) and PRE_OPTIMIZATION_TRACKER.md
(status column), then computes all summary numbers and compares them against
the tracker's Summary section.

Prevents report drift: numbers always derived from data, never manual counts.

Usage:
    python3 -m phionyx_core.research_engine.cli.verify_tracker [--stamp] [--json]
    python3 phionyx_core/research_engine/cli/verify_tracker.py [--stamp] [--json]

Options:
    --stamp  Write verification timestamp + PASS/FAIL into tracker header
    --json   Output full tracker report as JSON (for API / Founder Console)
"""

import json
import re
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

# ── Paths ──

REPO_ROOT = Path(__file__).resolve().parent
while REPO_ROOT != REPO_ROOT.parent:
    if (REPO_ROOT / ".git").exists():
        break
    REPO_ROOT = REPO_ROOT.parent

SURFACES_PATH = REPO_ROOT / "phionyx_core" / "research_engine" / "mutation" / "surfaces.yaml"
TRACKER_PATH = REPO_ROOT / "docs" / "PRE_OPTIMIZATION_TRACKER.md"
PROBE_PATH = REPO_ROOT / "phionyx_core" / "research_engine" / "evaluation" / "quality_probe.py"


# ── Surface data ──

def load_surfaces() -> list[dict]:
    """Load all surface entries from surfaces.yaml."""
    with open(SURFACES_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("surfaces", [])


def count_params(surfaces: list[dict]) -> dict:
    """Count parameters by tier, file, etc."""
    tier_a_params = []
    tier_c_params = []
    source_files = set()

    for s in surfaces:
        tier = s.get("tier", "").upper()
        params = s.get("parameters", [])
        if not params:
            continue

        source_files.add(s["file"])

        for p in params:
            entry = {
                "name": p["name"],
                "file": s["file"],
                "tier": tier,
                "agi_domain": s.get("agi_domain", "unclassified"),
                "mind_loop_stage": s.get("mind_loop_stage", "unclassified"),
            }
            if tier == "A":
                tier_a_params.append(entry)
            elif tier == "C":
                tier_c_params.append(entry)

    return {
        "tier_a": tier_a_params,
        "tier_c": tier_c_params,
        "total": len(tier_a_params) + len(tier_c_params),
        "source_files": source_files,
    }


def _build_agi_lookup(surfaces: list[dict]) -> dict[str, dict]:
    """Build param_name → {agi_domain, mind_loop_stage, continuity_impact, self_model_impact} lookup from surfaces.yaml."""
    lookup = {}
    for s in surfaces:
        agi_domain = s.get("agi_domain", "unclassified")
        mind_loop_stage = s.get("mind_loop_stage", "unclassified")
        continuity_impact = _infer_continuity_impact(agi_domain)
        self_model_impact = _infer_self_model_impact(agi_domain)
        for p in s.get("parameters", []):
            lookup[p["name"]] = {
                "agi_domain": agi_domain,
                "mind_loop_stage": mind_loop_stage,
                "continuity_impact": continuity_impact,
                "self_model_impact": self_model_impact,
            }
    return lookup


# Domain → continuity impact mapping (Learning Gate Contract / AGI architecture)
_CONTINUITY_MAP: dict[str, str] = {
    "memory": "cognitive",
    "meta": "cognitive",
    "physics": "none",
    "causality": "state",
    "social": "state",
    "planning": "cognitive",
    "world": "state",
    "governance": "none",
}

# Domain → self-model impact mapping
_SELF_MODEL_MAP: dict[str, str] = {
    "memory": "none",
    "meta": "confidence",
    "physics": "none",
    "causality": "none",
    "social": "none",
    "planning": "capability",
    "world": "none",
    "governance": "none",
}


def _infer_continuity_impact(agi_domain: str) -> str:
    """Infer continuity impact from AGI domain."""
    return _CONTINUITY_MAP.get(agi_domain, "none")


def _infer_self_model_impact(agi_domain: str) -> str:
    """Infer self-model impact from AGI domain."""
    return _SELF_MODEL_MAP.get(agi_domain, "none")


# ── Tracker status parsing ──

def parse_tracker_statuses(tracker_text: str) -> dict[str, str]:
    """Parse parameter statuses from tracker markdown tables.

    Returns {param_name: status} e.g. {"DEFAULT_GAMMA": "OPTIMIZED"}.
    """
    statuses = {}
    # Match table rows: | # | name | file | tier | STATUS | ...
    pattern = re.compile(
        r"^\|\s*\d+\s*\|\s*(\S+)\s*\|[^|]+\|[^|]+\|\s*(\w+)\s*\|",
        re.MULTILINE,
    )
    for m in pattern.finditer(tracker_text):
        name = m.group(1)
        status = m.group(2).upper()
        statuses[name] = status
    return statuses


# ── CQS slot mapping from tracker ──

def parse_cqs_slots(tracker_text: str) -> dict[str, str]:
    """Parse CQS slot assignments from tracker markdown tables.

    Returns {param_name: cqs_slot} e.g. {"DEFAULT_GAMMA": "C5"}.
    """
    slots = {}
    # Match: | # | name | file | tier | status | CQS_SLOT | ...
    pattern = re.compile(
        r"^\|\s*\d+\s*\|\s*(\S+)\s*\|[^|]+\|[^|]+\|[^|]+\|\s*(\S+)\s*\|",
        re.MULTILINE,
    )
    for m in pattern.finditer(tracker_text):
        name = m.group(1)
        slot = m.group(2).strip()
        slots[name] = slot
    return slots


# ── Probe metric counting ──

def count_probe_metrics() -> tuple[int, list[str]]:
    """Count probe metrics from quality_probe.py source.

    Parses _default_*_metrics() methods which list every metric key explicitly.
    More reliable than regex on return dicts (avoids false positives from sample data).
    Returns (total_metrics, domain_list).
    """
    if not PROBE_PATH.exists():
        return 0, []

    text = PROBE_PATH.read_text()

    # Find all _probe_* method definitions
    domains = re.findall(r"def (_probe_\w+)\(self\)", text)

    # Parse metric keys from _default_*_metrics() return dicts.
    # These are the canonical metric lists — one per domain, always "key": 0.5.
    # More reliable than regex on return dicts (avoids sample data false positives).
    metric_keys = set()
    in_default = False
    for line in text.split("\n"):
        if "_default_" in line and "_metrics" in line:
            in_default = True
            continue
        if in_default:
            m = re.match(r'\s+"(\w+)":\s*0\.5', line)
            if m:
                metric_keys.add(m.group(1))
            elif line.strip() == "}":
                in_default = False

    return len(metric_keys), [d.replace("_probe_", "") for d in domains]


# ── Compute expected summary ──

def compute_summary(surfaces: list[dict], tracker_text: str) -> dict:
    """Compute all summary numbers from source data."""
    counts = count_params(surfaces)
    statuses = parse_tracker_statuses(tracker_text)
    cqs_slots = parse_cqs_slots(tracker_text)
    n_metrics, probe_domains = count_probe_metrics()

    # Status counts
    status_counts = Counter(statuses.values())
    optimized = status_counts.get("OPTIMIZED", 0)
    gold = status_counts.get("GOLD", 0)
    experimented = status_counts.get("EXPERIMENTED", 0)
    covered = status_counts.get("COVERED", 0)

    # Optimized includes gold (gold is subset of optimized)
    total_optimized = optimized + gold
    total_experimented = total_optimized + experimented

    # CQS slot distribution for Tier A only
    cqs_distribution = Counter()
    cqs_optimized = Counter()
    for name, slot in cqs_slots.items():
        status = statuses.get(name, "COVERED")
        # Only count Tier A params
        if any(p["name"] == name and p["tier"] == "A" for p in counts["tier_a"]):
            cqs_distribution[slot] += 1
            if status in ("OPTIMIZED", "GOLD"):
                cqs_optimized[slot] += 1

    # CQS-driving = non-diagnostic Tier A
    cqs_driving = sum(
        1 for name, slot in cqs_slots.items()
        if slot != "diagnostic" and slot != "-"
        and any(p["name"] == name and p["tier"] == "A" for p in counts["tier_a"])
    )
    diagnostic_a = sum(
        1 for name, slot in cqs_slots.items()
        if slot == "diagnostic"
        and any(p["name"] == name and p["tier"] == "A" for p in counts["tier_a"])
    )

    return {
        "total_tunable": counts["total"],
        "tier_a": len(counts["tier_a"]),
        "tier_c": len(counts["tier_c"]),
        "source_files": len(counts["source_files"]),
        "cqs_driving": cqs_driving,
        "diagnostic_a": diagnostic_a,
        "probe_domains": len(probe_domains),
        "probe_metrics": n_metrics,
        "total_optimized": total_optimized,
        "gold": gold,
        "total_experimented": total_experimented,
        "covered": covered,
        "cqs_distribution": dict(cqs_distribution),
        "cqs_optimized": dict(cqs_optimized),
    }


# ── Full table parsers (for JSON export) ──

def _parse_full_param_table(tracker_text: str) -> list[dict]:
    """Parse all parameter rows from the Full Parameter Table sections.

    Each row: | # | name | file | tier | status | cqs_slot | probe_domain | value | range |
    """
    params = []
    # Match 9-column param rows across all Adim sections
    pattern = re.compile(
        r"^\|\s*\d+\s*\|"            # | # |
        r"\s*\*?\*?(\S+?)\*?\*?\s*\|"  # | name (possibly bold) |
        r"\s*([^|]+?)\s*\|"          # | file |
        r"\s*(\w+)\s*\|"             # | tier |
        r"\s*(\w+)\s*\|"             # | status |
        r"\s*([^|]+?)\s*\|"          # | cqs_slot |
        r"\s*([^|]*?)\s*\|"          # | probe_domain |
        r"\s*([^|]+?)\s*\|"          # | value |
        r"\s*([^|]+?)\s*\|",         # | range |
        re.MULTILINE,
    )
    valid_statuses = {"COVERED", "EXPERIMENTED", "OPTIMIZED", "GOLD", "NOT_TUNABLE"}
    for m in pattern.finditer(tracker_text):
        status = m.group(4).strip()
        if status not in valid_statuses:
            continue
        params.append({
            "name": m.group(1).strip("*"),
            "file": m.group(2).strip(),
            "tier": m.group(3).strip(),
            "status": status,
            "cqs_slot": m.group(5).strip(),
            "probe_domain": m.group(6).strip(),
            "value": m.group(7).strip(),
            "range": m.group(8).strip(),
        })
    return params


def _parse_candidates(tracker_text: str) -> list[dict]:
    """Parse Next Best Candidates table.

    Row: | Pri | Parameter | File | CQS Slot | Readiness | Sensitivity | Risk | Est. Exps | Rationale |
    """
    candidates = []
    # Find the candidates section
    section = re.search(
        r"## Next Best Candidates.*?\n(.*?)(?=\n---|\n## |\Z)",
        tracker_text,
        re.DOTALL,
    )
    if not section:
        return candidates

    pattern = re.compile(
        r"^\|\s*(\d+)\s*\|"           # | pri |
        r"\s*([^|]+?)\s*\|"           # | parameter |
        r"\s*([^|]+?)\s*\|"           # | file |
        r"\s*([^|]+?)\s*\|"           # | cqs_slot |
        r"\s*([^|]+?)\s*\|"           # | readiness |
        r"\s*([^|]+?)\s*\|"           # | sensitivity |
        r"\s*([^|]+?)\s*\|"           # | risk |
        r"\s*~?(\d+)\s*\|"            # | est_exps |
        r"\s*([^|]+?)\s*\|",          # | rationale |
        re.MULTILINE,
    )
    for m in pattern.finditer(section.group(1)):
        candidates.append({
            "priority": int(m.group(1)),
            "param": m.group(2).strip(),
            "file": m.group(3).strip(),
            "cqs_slot": m.group(4).strip(),
            "readiness": m.group(5).strip(),
            "sensitivity": m.group(6).strip(),
            "risk": m.group(7).strip(),
            "est_exps": int(m.group(8)),
            "rationale": m.group(9).strip(),
        })
    return candidates


def _parse_campaign_policy(tracker_text: str) -> dict:
    """Parse Slot-Level Campaign Policy table.

    Row: | Policy | Slots | Action |
    Returns: {slot: {priority, rationale}} for each slot mentioned.
    """
    policy = {}
    section = re.search(
        r"### Slot-Level Campaign Policy.*?\n(.*?)(?=\n---|\n## |\Z)",
        tracker_text,
        re.DOTALL,
    )
    if not section:
        return policy

    pattern = re.compile(
        r"^\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|"  # | policy |
        r"\s*([^|]+?)\s*\|"                   # | slots |
        r"\s*([^|]+?)\s*\|",                  # | action |
        re.MULTILINE,
    )
    for m in pattern.finditer(section.group(1)):
        priority_name = m.group(1).strip()
        slots_str = m.group(2).strip()
        action = m.group(3).strip()
        # Skip header/separator rows
        if priority_name.lower() in ("policy", "---", "") or "---" in priority_name:
            continue
        # Parse individual slots (e.g. "C3, C4" or "diagnostic")
        for slot in re.split(r"[,\s]+", slots_str):
            slot = slot.strip()
            if slot:
                policy[slot] = {"priority": priority_name, "rationale": action}
    return policy


def _parse_module_summary(tracker_text: str) -> dict:
    """Parse Module Summary table.

    Row: | Module | Source Files | Tunables | RE-Experimented | RE-Optimized | Pre-Existing | Gold | ... |
    """
    modules = {}
    section = re.search(
        r"## Module Summary.*?\n(.*?)(?=\n---|\n## |\Z)",
        tracker_text,
        re.DOTALL,
    )
    if not section:
        return modules

    pattern = re.compile(
        r"^\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|"  # | module |
        r"\s*([^|]+?)\s*\|"                   # | source files |
        r"\s*\*?\*?(\d+)[^|]*\*?\*?\s*\|"    # | tunables (may have parenthetical) |
        r"\s*\*?\*?(\d+)\*?\*?\s*\|"          # | re-experimented |
        r"\s*\*?\*?(\d+)\*?\*?\s*\|"          # | re-optimized |
        r"\s*(\d+)\s*\|"                      # | pre-existing |
        r"\s*(\d+)\s*\|",                     # | gold |
        re.MULTILINE,
    )
    for m in pattern.finditer(section.group(1)):
        name = m.group(1).strip()
        if name.lower() in ("module", "---", "**total**", "total"):
            continue
        modules[name] = {
            "total": int(m.group(3)),
            "re_experimented": int(m.group(4)),
            "re_optimized": int(m.group(5)),
            "pre_existing": int(m.group(6)),
            "gold": int(m.group(7)),
        }
    return modules


def _parse_lineage(tracker_text: str) -> list[dict]:
    """Parse Optimization Lineage table (RE-Optimized Parameters).

    Row: | # | Parameter | Experiments | KEEP | Delta CQS | Baseline Date | Gold Date | Note |
    """
    lineage = []
    section = re.search(
        r"### RE-Optimized Parameters.*?\n(.*?)(?=\n###|\n---|\n## |\Z)",
        tracker_text,
        re.DOTALL,
    )
    if not section:
        return lineage

    pattern = re.compile(
        r"^\|\s*\d+\s*\|"              # | # |
        r"\s*\*?\*?([^|*]+?)\*?\*?\s*\|"  # | parameter |
        r"\s*(\d+)\s*\|"               # | experiments |
        r"\s*(\d+)\s*\|"               # | keep |
        r"\s*\*?\*?([^|*]+?)\*?\*?\s*\|"  # | delta cqs |
        r"\s*([^|]+?)\s*\|"            # | baseline date |
        r"\s*([^|]+?)\s*\|"            # | gold date |
        r"\s*([^|]+?)\s*\|",           # | note |
        re.MULTILINE,
    )
    for m in pattern.finditer(section.group(1)):
        lineage.append({
            "param": m.group(1).strip(),
            "experiments": int(m.group(2)),
            "keep_count": int(m.group(3)),
            "best_delta": m.group(4).strip(),
            "baseline_date": m.group(5).strip(),
            "gold_date": m.group(6).strip(),
            "note": m.group(7).strip(),
        })
    return lineage


def _build_heatmap(computed: dict) -> dict:
    """Build enriched CQS slot heatmap from computed summary."""
    heatmap = {}
    for slot, total in computed["cqs_distribution"].items():
        optimized = computed["cqs_optimized"].get(slot, 0)
        heatmap[slot] = {
            "total": total,
            "optimized": optimized,
            "backlog": total - optimized,
        }
    return heatmap


def _compute_signal_scores(
    candidates: list[dict],
    heatmap: dict,
    params: list[dict],
    surfaces: list[dict],
) -> list[dict]:
    """Compute composite signal score for each candidate.

    Score = readiness * slot_scarcity * range_factor * constraint_penalty

    - readiness: [0,1] probe metric value (higher = more signal)
    - slot_scarcity: backlog/total for that CQS slot (higher = more needed)
    - range_factor: normalized range width (wider range = more exploration value)
    - constraint_penalty: 1.0 for unconstrained, 0.7 for sum=1 constraints
    """
    # Build constraint set from surfaces.yaml
    constrained = set()
    for s in surfaces:
        for c in s.get("constraints", []):
            for p in c.get("params", []):
                constrained.add(p)

    # Build range map from params table
    range_map = {}
    for p in params:
        name = p["name"]
        rng = p.get("range", "")
        try:
            parts = rng.strip("[]").split(",")
            lo, hi = float(parts[0].strip()), float(parts[1].strip())
            range_map[name] = hi - lo
        except (ValueError, IndexError):
            range_map[name] = 0.0

    max_range = max(range_map.values()) if range_map else 1.0

    for c in candidates:
        # readiness
        try:
            readiness = float(c.get("readiness", 0))
        except ValueError:
            readiness = 0.5

        # slot_scarcity: what fraction of slot is still backlog
        slot = c.get("cqs_slot", "")
        slot_info = heatmap.get(slot, {})
        total = slot_info.get("total", 1)
        backlog = slot_info.get("backlog", 1)
        slot_scarcity = backlog / max(total, 1)

        # range_factor: normalized to [0.2, 1.0]
        rw = range_map.get(c.get("param", ""), 0.0)
        range_factor = 0.2 + 0.8 * (rw / max_range) if max_range > 0 else 0.5

        # constraint_penalty
        constraint_penalty = 0.7 if c.get("param", "") in constrained else 1.0

        score = round(readiness * slot_scarcity * range_factor * constraint_penalty, 3)
        c["signal_score"] = score

    # Re-sort by signal_score descending
    candidates.sort(key=lambda x: x.get("signal_score", 0), reverse=True)
    return candidates


def _parse_audit_linkage(lineage: list[dict]) -> list[dict]:
    """Enrich lineage entries with experiment IDs and audit events.

    Uses experiments.jsonl (has parameter_name) + audit.jsonl (has decision/cqs_delta).
    """
    exp_path = REPO_ROOT / "data" / "research_engine" / "experiments.jsonl"
    audit_path = REPO_ROOT / "data" / "research_engine" / "audit" / "audit.jsonl"

    # Build param → [experiment records] from experiments.jsonl
    param_experiments: dict[str, list[dict]] = {}
    if exp_path.exists():
        try:
            for line in exp_path.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    pname = rec.get("hypothesis", {}).get("parameter_name", "")
                    if pname:
                        param_experiments.setdefault(pname, []).append({
                            "experiment_id": rec.get("experiment_id", ""),
                            "decision": rec.get("decision", ""),
                            "cqs_delta": rec.get("cqs_delta", 0),
                            "value": rec.get("hypothesis", {}).get("new_value"),
                        })
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

    # Build experiment_id set from audit for cross-reference
    audit_ids = set()
    if audit_path.exists():
        try:
            for line in audit_path.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                    eid = ev.get("experiment_id", "")
                    if eid:
                        audit_ids.add(eid)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

    for entry in lineage:
        param = entry.get("param", "")
        exps = param_experiments.get(param, [])
        entry["audit_experiment_ids"] = [e["experiment_id"] for e in exps]
        entry["audit_event_count"] = len(exps)
        entry["audit_in_trail"] = sum(
            1 for e in exps if e["experiment_id"] in audit_ids
        )
        entry["experiment_decisions"] = {
            "keep": sum(1 for e in exps if e["decision"] == "keep"),
            "revert": sum(1 for e in exps if e["decision"] == "revert"),
        }

    return lineage


# ── JSON report builder ──

def build_json_report() -> dict:
    """Build full tracker report as JSON dict for API consumption."""
    surfaces = load_surfaces()
    tracker_text = TRACKER_PATH.read_text()
    computed = compute_summary(surfaces, tracker_text)

    # Run verification quietly (capture errors)
    errors = []
    if SURFACES_PATH.exists() and TRACKER_PATH.exists():
        claimed = extract_tracker_summary(tracker_text)
        checks = [
            ("total tunable params", computed["total_tunable"]),
            ("tier a (autonomous)", computed["tier_a"]),
            ("tier c (governance, proposal-only)", computed["tier_c"]),
            ("source files", computed["source_files"]),
            ("probe domains", computed["probe_domains"]),
            ("probe metrics", computed["probe_metrics"]),
        ]
        for label, expected in checks:
            found = claimed.get(label)
            if found is None:
                for k, v in claimed.items():
                    if label.split()[0] in k:
                        found = v
                        break
            if found is not None and found != expected:
                errors.append(f"MISMATCH: '{label}' — tracker says {found}, computed {expected}")
        if computed["cqs_driving"] + computed["diagnostic_a"] != computed["tier_a"]:
            errors.append(
                f"MISMATCH: CQS-driving ({computed['cqs_driving']}) + "
                f"diagnostic ({computed['diagnostic_a']}) != Tier A ({computed['tier_a']})"
            )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = _parse_full_param_table(tracker_text)
    # Enrich params with AGI domain/stage from surfaces.yaml
    agi_lookup = _build_agi_lookup(surfaces)
    for p in params:
        key = p["name"]
        if key in agi_lookup:
            p["agi_domain"] = agi_lookup[key]["agi_domain"]
            p["mind_loop_stage"] = agi_lookup[key]["mind_loop_stage"]
            p["continuity_impact"] = agi_lookup[key]["continuity_impact"]
            p["self_model_impact"] = agi_lookup[key]["self_model_impact"]
        else:
            p["agi_domain"] = "unclassified"
            p["mind_loop_stage"] = "unclassified"
            p["continuity_impact"] = "none"
            p["self_model_impact"] = "none"
    heatmap = _build_heatmap(computed)
    candidates = _parse_candidates(tracker_text)
    candidates = _compute_signal_scores(candidates, heatmap, params, surfaces)
    lineage = _parse_lineage(tracker_text)
    lineage = _parse_audit_linkage(lineage)

    # AGI domain summary
    agi_summary = {}
    for p in params:
        domain = p.get("agi_domain", "unclassified")
        if domain not in agi_summary:
            agi_summary[domain] = {"total": 0, "optimized": 0, "gold": 0}
        agi_summary[domain]["total"] += 1
        if p.get("status") in ("OPTIMIZED", "GOLD"):
            agi_summary[domain]["optimized"] += 1
        if p.get("status") == "GOLD":
            agi_summary[domain]["gold"] += 1

    # Continuity and self-model impact distribution
    continuity_dist: dict[str, int] = {}
    self_model_dist: dict[str, int] = {}
    for p in params:
        ci = p.get("continuity_impact", "none")
        si = p.get("self_model_impact", "none")
        continuity_dist[ci] = continuity_dist.get(ci, 0) + 1
        self_model_dist[si] = self_model_dist.get(si, 0) + 1

    # AGI campaign summary — aggregates continuity and self-model experiments
    agi_campaign_summary = {
        "total_agi_experiments": sum(
            v["total"] for v in agi_summary.values()
            if v.get("total", 0) > 0
        ),
        "domain_coverage": {
            domain: data["total"]
            for domain, data in agi_summary.items()
            if data.get("total", 0) > 0
        },
        "continuity_experiments": continuity_dist.get("cognitive", 0)
        + continuity_dist.get("structural", 0)
        + continuity_dist.get("retrieval", 0),
        "self_model_experiments": self_model_dist.get("capability", 0)
        + self_model_dist.get("confidence", 0)
        + self_model_dist.get("identity", 0),
        "net_cqs_impact": f"+{computed.get('cqs_delta', 0.0):.3f}",
    }

    return {
        "summary": computed,
        "parameters": params,
        "candidates": candidates,
        "campaign_policy": _parse_campaign_policy(tracker_text),
        "module_summary": _parse_module_summary(tracker_text),
        "heatmap": heatmap,
        "lineage": lineage,
        "agi_summary": agi_summary,
        "agi_campaign_summary": agi_campaign_summary,
        "continuity_impact_distribution": continuity_dist,
        "self_model_impact_distribution": self_model_dist,
        "verification": {
            "passed": len(errors) == 0,
            "timestamp": now,
            "errors": errors,
        },
    }


# ── Verify ──

def extract_tracker_summary(tracker_text: str) -> dict[str, str]:
    """Extract claimed values from the tracker Summary table."""
    claimed = {}
    # Pattern: | **label** | value | note |
    for m in re.finditer(
        r"^\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|\s*(\d+)\s*\|",
        tracker_text,
        re.MULTILINE,
    ):
        label = m.group(1).strip().lower()
        value = int(m.group(2))
        claimed[label] = value
    return claimed


def verify(fix: bool = False) -> bool:
    """Run verification. Returns True if all checks pass."""
    if not SURFACES_PATH.exists():
        print(f"ERROR: surfaces.yaml not found at {SURFACES_PATH}")
        return False
    if not TRACKER_PATH.exists():
        print(f"ERROR: Tracker not found at {TRACKER_PATH}")
        return False

    surfaces = load_surfaces()
    tracker_text = TRACKER_PATH.read_text()
    computed = compute_summary(surfaces, tracker_text)

    print("=" * 60)
    print("PRE Optimization Tracker — Verification Report")
    print("=" * 60)
    print()

    # Show computed values
    print("Computed from surfaces.yaml + tracker statuses:")
    print(f"  Total tunable params : {computed['total_tunable']}")
    print(f"  Tier A (autonomous)  : {computed['tier_a']}")
    print(f"    CQS-driving        : {computed['cqs_driving']}")
    print(f"    Diagnostic         : {computed['diagnostic_a']}")
    print(f"  Tier C (governance)  : {computed['tier_c']}")
    print(f"  Source files         : {computed['source_files']}")
    print(f"  Probe domains        : {computed['probe_domains']}")
    print(f"  Probe metrics        : {computed['probe_metrics']}")
    print(f"  Optimized (inc gold) : {computed['total_optimized']}")
    print(f"    Gold               : {computed['gold']}")
    print(f"  Experimented total   : {computed['total_experimented']}")
    print(f"  Remaining COVERED    : {computed['covered']}")
    print()

    # CQS slot distribution
    print("CQS Slot Distribution (Tier A):")
    for slot in sorted(computed["cqs_distribution"]):
        total = computed["cqs_distribution"][slot]
        opt = computed["cqs_optimized"].get(slot, 0)
        print(f"  {slot:12s}: {total:3d} params, {opt} optimized")
    print()

    # Cross-check with tracker summary
    claimed = extract_tracker_summary(tracker_text)
    errors = []

    checks = [
        ("total tunable params", computed["total_tunable"]),
        ("tier a (autonomous)", computed["tier_a"]),
        ("tier c (governance, proposal-only)", computed["tier_c"]),
        ("source files", computed["source_files"]),
        ("probe domains", computed["probe_domains"]),
        ("probe metrics", computed["probe_metrics"]),
    ]

    for label, expected in checks:
        found = claimed.get(label)
        if found is None:
            # Try partial match
            for k, v in claimed.items():
                if label.split()[0] in k:
                    found = v
                    break
        if found is not None and found != expected:
            errors.append(f"  MISMATCH: '{label}' — tracker says {found}, computed {expected}")

    # Verify Tier A = CQS-driving + diagnostic
    if computed["cqs_driving"] + computed["diagnostic_a"] != computed["tier_a"]:
        errors.append(
            f"  MISMATCH: CQS-driving ({computed['cqs_driving']}) + "
            f"diagnostic ({computed['diagnostic_a']}) != "
            f"Tier A ({computed['tier_a']})"
        )

    if errors:
        print("ERRORS FOUND:")
        for e in errors:
            print(e)
        print()
        return False
    else:
        print("ALL CHECKS PASSED")
        return True


def stamp_tracker(passed: bool) -> None:
    """Write verification timestamp + PASS/FAIL into tracker header."""
    if not TRACKER_PATH.exists():
        return

    text = TRACKER_PATH.read_text()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status = "PASS" if passed else "FAIL"

    text = re.sub(
        r"<!-- VERIFY_TIMESTAMP -->.*?<!-- /VERIFY_TIMESTAMP -->",
        f"<!-- VERIFY_TIMESTAMP -->{now}<!-- /VERIFY_TIMESTAMP -->",
        text,
    )
    text = re.sub(
        r"<!-- VERIFY_STATUS -->.*?<!-- /VERIFY_STATUS -->",
        f"<!-- VERIFY_STATUS -->{status}<!-- /VERIFY_STATUS -->",
        text,
    )

    TRACKER_PATH.write_text(text)
    print(f"\nStamped tracker: {now} — {status}")


def main():
    if "--json" in sys.argv:
        report = build_json_report()
        print(json.dumps(report, ensure_ascii=False))
        sys.exit(0 if report["verification"]["passed"] else 1)

    stamp = "--stamp" in sys.argv
    ok = verify()
    if stamp:
        stamp_tracker(ok)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
