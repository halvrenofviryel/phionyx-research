#!/usr/bin/env python3
"""Claim-language gate — lints every registered artefact's live README against portfolio.yaml.

The registry (portfolio.yaml, repo root) is the single source of truth for what the
portfolio may claim. A claim strengthens by flipping a registry flag in a reviewed
commit WITH evidence — never in README prose first. This linter enforces that ordering.

Rules (each conditional on registry flags; all matching is case-insensitive and
negation-aware — "not independently verified" is correct usage and never flagged):

  A1  "profile of AIREP"                              banned while no artefact has
      airep_relationship: profile_of (none today)
  A2  AIREP conformance/production claims             ("implements AIREP", "AIREP-conformant",
      "conform(s|ing) to AIREP", "produces/emits an AIREP record", "into an AIREP record")
      banned unless airep_relationship: self (the spec repo must talk about records)
  S1  "signed by default"                             banned while signing_default != signed
  V1  "independently verified/reproduced/validated/confirmed"
                                                      banned while external_validation: false
  V2  "independent verifier(s)"                       banned (use "cross-language first-party
      verifier implementations"); "independent producer" stays legal
  T1  "tamper-evident"                                banned un-negated (state the threat model
      or negate); registry exception with reason otherwise
  R1  "replayable"                                    banned when the artefact declares
      replay_semantics: none (the registry must state WHICH replay is meant)
  P1  "production-ready" / "certified" / "guaranteed" / "battle-tested"
                                                      banned un-negated, portfolio-wide
  X1  sibling version pin                             a README may state only its OWN version;
      a line naming another registered artefact together with a vX.Y token is flagged
      (measured-equivalence pins go in allowed_exceptions with a reason)

Exit codes: 0 clean · 1 violations · 2 fetch/parse failure (a README that cannot be
read is NOT a pass) · 3 self-test failure (the gate could not prove its rules fire).

Usage:  python tools/claim_lint.py [--self-test-only] [--skip-fetch NAME ...]
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("claim_lint: pyyaml required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
GITHUB_OWNER = "halvrenofviryel"

NEGATORS = re.compile(
    r"\b(not|no|non|never|nothing|without|neither|nor|isn'?t|aren'?t|hasn'?t|haven'?t|yet)\b[^.]{0,55}$",
    re.IGNORECASE,
)


def _negated(text: str, start: int) -> bool:
    """True when a negator appears shortly before the match, in the same sentence."""
    window = text[max(0, start - 70):start]
    return bool(NEGATORS.search(window))


RULES: list[tuple[str, re.Pattern, str, bool]] = [
    # (rule id, pattern, condition key, negation_exempts)
    ("A1", re.compile(r"profile of (the )?(AI Runtime Evidence Protocol|AIREP)", re.I), "airep", False),
    ("A2", re.compile(
        r"(implement\w*\s+AIREP|AIREP-conformant|conform\w*\s+to\s+(the\s+)?AIREP"
        r"|produc\w*\s+(an\s+)?AIREP record|emit\w*\s+AIREP records?|into an AIREP record"
        r"|as an AIREP (evidence )?record)", re.I), "airep", True),
    ("S1", re.compile(r"(?<![a-z])signed by default", re.I), "signing", True),
    ("V1", re.compile(r"independently (verified|reproduced|validated|confirmed)", re.I), "external", True),
    ("V2", re.compile(r"independent verifiers?\b", re.I), "external", True),
    ("T1", re.compile(r"tamper[- ]evident", re.I), "always", True),
    ("R1", re.compile(r"replayable", re.I), "replay_none", True),
    ("P1", re.compile(r"(production[- ]ready|certified|guaranteed|battle[- ]tested)", re.I), "always", True),
]

SIBLING_VERSION = re.compile(r"(\bv\d+\.\d+(\.\d+)?|\b\d+\.\d+\.\d+)([ab]\d+|rc\d+)?(\.[xX])?\b")


def _rule_applies(cond: str, art: dict) -> bool:
    if cond == "airep":
        return art.get("airep_relationship") != "self"
    if cond == "signing":
        return art.get("signing_default") != "signed"
    if cond == "external":
        return not art.get("external_validation", False)
    if cond == "replay_none":
        sem = art.get("replay_semantics")
        return sem in (None, "none", [], ["none"])
    return True  # "always"


def _fetch(spec: str) -> str:
    if spec.startswith("local:"):
        return (ROOT / spec[len("local:"):]).read_text(encoding="utf-8")
    with urllib.request.urlopen(spec, timeout=30) as r:  # noqa: S310 — pinned https URLs from the registry
        return r.read().decode("utf-8")


def _excepted(line: str, art: dict) -> str | None:
    for exc in art.get("allowed_exceptions", []) or []:
        if exc.get("text") and exc["text"] in line:
            return exc.get("reason", "excepted")
    return None


def lint_artifact(name: str, art: dict, text: str, aliases: dict[str, str],
                  spec_versions: dict[str, list[str]] | None = None) -> list[str]:
    spec_versions = spec_versions or {}
    violations: list[str] = []
    lines = text.splitlines()
    for rule_id, pat, cond, neg_ok in RULES:
        if not _rule_applies(cond, art):
            continue
        for m in pat.finditer(text):
            if neg_ok and _negated(text, m.start()):
                continue
            line_no = text.count("\n", 0, m.start()) + 1
            line = lines[line_no - 1]
            if _excepted(line, art):
                continue
            violations.append(f"{name}: {rule_id} L{line_no}: …{line.strip()[:120]}")
    # X1 — sibling RELEASE-version pins: a version token within 40 chars after a sibling
    # alias (hyphen-safe boundaries). Spec-version mentions far from the name don't count.
    for i, line in enumerate(lines, 1):
        if not SIBLING_VERSION.search(line):
            continue
        for alias, owner in aliases.items():
            if owner == name:
                continue
            for am in re.finditer(rf"(?<![\w-]){re.escape(alias)}(?![\w-])", line):
                window = line[am.end():am.end() + 40]
                vm = SIBLING_VERSION.search(window)
                if vm:
                    if vm.group(0) in (spec_versions.get(owner) or []):
                        continue
                    if _excepted(line, art):
                        break
                    violations.append(f"{name}: X1 L{i} (names {alias}): …{line.strip()[:120]}")
                    break
            else:
                continue
            break
    return violations


# --- self-test: every rule must be able to fire, and negation must exempt -------------
SELF_TEST = [
    ("A1", "RGE is a Phionyx profile of AIREP.", {"airep_relationship": "developed_toward"}, True),
    ("A1", "RGE is a Phionyx profile of AIREP.", {"airep_relationship": "self"}, False),
    ("A2", "the runtime produces an AIREP record per turn", {}, True),
    ("A2", "does not produce an AIREP record today", {}, False),
    ("A2", "records the claim as an AIREP evidence record", {}, True),
    ("S1", "every envelope is signed by default", {}, True),
    ("V1", "results were independently verified", {}, True),
    ("V1", "nothing here has been independently verified", {}, False),
    ("V1", "results were independently verified", {"external_validation": True}, False),
    ("V2", "checked by two independent verifiers", {}, True),
    ("T1", "a tamper-evident audit chain", {}, True),
    ("T1", "Not tamper-evident. The stream is in-process state.", {}, False),
    ("R1", "replayable evidence", {"replay_semantics": "none"}, True),
    ("R1", "replayable evidence", {"replay_semantics": ["verification_replay"]}, False),
    ("P1", "production-ready governance", {}, True),
    ("P1", "not battle-tested", {}, False),
]


def self_test() -> bool:
    ok = True
    for rule_id, text, art, should_fire in SELF_TEST:
        hits = [v for v in lint_artifact("selftest", art, text, {}) if f" {rule_id} " in v]
        if bool(hits) != should_fire:
            print(f"SELF-TEST FAIL: {rule_id} on {text!r} (art={art}) — "
                  f"expected fire={should_fire}, got {bool(hits)}", file=sys.stderr)
            ok = False
    # X1 fixture
    aliases = {"phionyx-core": "phionyx-research", "phionyx-eval": "phionyx-eval"}
    x1 = lint_artifact("phionyx-eval", {}, "works with phionyx-core v0.9.0", aliases)
    if not any(" X1 " in v for v in x1):
        print("SELF-TEST FAIL: X1 did not fire on a sibling version pin", file=sys.stderr)
        ok = False
    x1_own = lint_artifact("phionyx-research", {}, "phionyx-core v0.9.0 on PyPI", aliases)
    if any(" X1 " in v for v in x1_own):
        print("SELF-TEST FAIL: X1 fired on the artefact's OWN version", file=sys.stderr)
        ok = False
    far = lint_artifact("phionyx-eval", {}, "phionyx-core is the engine; " + "x" * 45 + " spec v0.1", aliases)
    if any(" X1 " in v for v in far):
        print("SELF-TEST FAIL: X1 fired on a far-away version token", file=sys.stderr)
        ok = False
    sub = lint_artifact("x", {}, "PHIONYX_LOG=v0.3.x phionyx-eval-inspect convert", {"phionyx-eval": "phionyx-eval"})
    if any(" X1 " in v for v in sub):
        print("SELF-TEST FAIL: alias matched inside a longer hyphenated name", file=sys.stderr)
        ok = False
    url = lint_artifact("x", {}, "see github.com/halvrenofviryel/foo (v0.9.9)", {"foo": "foo"})
    if any(" X1 " in v for v in url):
        pass  # foo IS adjacent to the version - this SHOULD fire; owner exclusion is main()-level
    uns = lint_artifact("x", {}, "envelopes are unsigned by default; configure a signer", {})
    if any(" S1 " in v for v in uns):
        print("SELF-TEST FAIL: S1 fired on 'unsigned by default'", file=sys.stderr)
        ok = False
    spec = lint_artifact("x", {}, "the ai-runtime-evidence-protocol (v0.1, experimental) format",
                         {"ai-runtime-evidence-protocol": "ai-runtime-evidence-protocol"},
                         {"ai-runtime-evidence-protocol": ["v0.1"]})
    if any(" X1 " in v for v in spec):
        print("SELF-TEST FAIL: X1 fired on a declared spec version", file=sys.stderr)
        ok = False
    doi = lint_artifact("x", {}, "measurement-axioms DOI 10.5281/zenodo.21763430", {"measurement-axioms": "measurement-axioms"})
    if any(" X1 " in v for v in doi):
        print("SELF-TEST FAIL: X1 fired on a DOI number", file=sys.stderr)
        ok = False
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test-only", action="store_true")
    ap.add_argument("--skip-fetch", nargs="*", default=[], help="artefact names to skip (offline debugging)")
    args = ap.parse_args()

    if not self_test():
        return 3
    print("self-test: all rules proved live (fire + negation-exempt)")
    if args.self_test_only:
        return 0

    reg = yaml.safe_load((ROOT / "portfolio.yaml").read_text(encoding="utf-8"))
    defaults = reg.get("defaults", {})
    artifacts: dict[str, dict] = reg["artifacts"]

    aliases: dict[str, str] = {}
    for name, art in artifacts.items():
        if name == GITHUB_OWNER:
            continue  # the org/profile name appears inside every repo URL — never a version-pin anchor
        aliases[name] = name
        src = (art or {}).get("release_source", "") or ""
        if src.startswith("pypi:"):
            aliases[src[len("pypi:"):]] = name

    spec_map = {n: (a or {}).get("spec_versions") or [] for n, a in artifacts.items()}
    failures: list[str] = []
    errors: list[str] = []
    for name, art in artifacts.items():
        art = {**defaults, **(art or {})}
        if art.get("status") == "archived":
            print(f"  skip {name} (archived — banner declares no new claims)")
            continue
        if name in args.skip_fetch:
            print(f"  skip {name} (--skip-fetch)")
            continue
        try:
            text = _fetch(art["readme"])
        except Exception as exc:  # noqa: BLE001 — an unreadable README is an ERROR, not a pass
            errors.append(f"{name}: FETCH ERROR {type(exc).__name__}: {exc}")
            continue
        vs = lint_artifact(name, art, text, aliases, spec_map)
        failures.extend(vs)
        print(f"  {name}: {'CLEAN' if not vs else f'{len(vs)} violation(s)'}")

    for v in failures:
        print("VIOLATION", v)
    for e in errors:
        print("ERROR", e, file=sys.stderr)
    if errors:
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
