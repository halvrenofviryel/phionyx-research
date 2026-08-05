"""State-leak detection and redaction for generated responses.

Extracted 2026-08-02 from ``phionyx_core/pipeline/blocks/archive/coherence_qa.py``
so the capability can run without a 47th canonical block.

**Why it was not running.** ``coherence_qa`` was canonical in v2.4.0 and appears
in v2.5.0's ``block_mapping.removed_blocks`` with no successor mapping and no
recorded rationale; the commit that introduced v2.5.0 is the rebrand commit, so
git carries no per-block reasoning either. It has been in ``blocks/archive/``
since ``709a0b04``. Meanwhile three runtime consumers kept waiting for its
output: ``response_build`` swaps in ``redacted_text`` when ``leak_detected``,
``echo_orchestrator`` has a redaction branch keyed on a block id no contract
version contains, and ``response_revision_gate`` has three rules on coherence.
Nineteen test files supplied ``coherence_qa_result`` by hand, so a whole test
file for coherence enforcement passed on input nothing produced.

**Why here rather than as block 47.** The canonical count is cited in published
papers, books and posts; adding a block makes those inconsistent. The
capability does not need its own block — it needs to run after the narrative
exists and before ``response_revision_gate`` (canonical 41) so the gate's
coherence rules can see it. ``ethics_post_response`` (canonical 21) is the
designated post-generation content check and sits in that window, so it hosts
this. The two alternatives measured — the ``response_serializer`` middleware
and ``response_build`` — both run after block 41 and would restore redaction
while leaving the gate's rules dead.

**Scope of the pattern set, stated because it is easy to over-read.** The
patterns match a metric *named with a value attached* — ``phi is 0.85``,
``entropy = 0.3``, ``valence: 0.2`` — plus a few bracketed and prefixed forms.
A bare mention such as "entropy 0.3", with no ``is``/``=``/``:``, is not
matched. That is the set as written, not a failure of it; widening it is a
separate decision with its own false-positive cost.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

#: Patterns that indicate internal state has reached the user-visible text.
#: Carried over verbatim from the archived block so behaviour is unchanged.
STATE_LEAK_PATTERNS = [
    r'\bphi\s*(?:is|[=:])\s*[\d.]+',
    r'\bentropy\s*(?:is|[=:])\s*[\d.]+',
    r'\bvalence\s*(?:is|[=:])\s*[\d.]+',
    r'\barousal\s*(?:is|[=:])\s*[\d.]+',
    r'\btrust\s*(?:is|[=:])\s*[\d.]+',
    r'\bcoherence\s*(?:is|[=:])\s*[\d.]+',
    r'\bdrive\s*(?:is|[=:])\s*[\d.]+',
    r'Current State:.*',
    r'State:.*phi',
    r'Metrics:.*',
    r'Internal:.*',
    r'Debug:.*',
    r'\[PHI\].*',
    r'\[ENTROPY\].*',
    r'\[VALENCE\].*',
    r'\bmy current phi\b',
    r'\bmy phi is\b',
    r'\bmy entropy is\b',
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in STATE_LEAK_PATTERNS]


def assess_coherence(narrative_text: str) -> Optional[Dict[str, Any]]:
    """Scan a generated response for internal-state leakage.

    Returns the ``coherence_qa_result`` shape the existing consumers already
    read, or ``None`` when there is no text to scan — an absent narrative is
    not a clean one, and the caller records that as a non-measurement rather
    than as a score.

    The scoring and redaction are unchanged from the archived block: one tenth
    off per violation, three tenths more if anything leaked, and the redacted
    text is the input with every matching span removed and whitespace collapsed.
    """
    if not narrative_text:
        return None

    violations: List[str] = []
    leak_detected = False
    for pattern in _COMPILED_PATTERNS:
        match = pattern.search(narrative_text)
        if match:
            violations.append(match.group())
            leak_detected = True

    score = 1.0 - (len(violations) * 0.1) - (0.3 if leak_detected else 0.0)
    score = max(0.0, min(1.0, score))

    redacted_text: Optional[str] = None
    if leak_detected:
        cleaned = narrative_text
        for pattern in _COMPILED_PATTERNS:
            cleaned = pattern.sub("", cleaned)
        redacted_text = re.sub(r"\s+", " ", cleaned).strip()

    return {
        "coherence_score": score,
        "leak_detected": leak_detected,
        "violations": violations,
        "violation_count": len(violations),
        "redacted_text": redacted_text,
    }
