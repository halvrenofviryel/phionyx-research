# Pull request draft — not submitted

## Title

Add bounded control-evidence research and offline reproduction packet

## Body

This change makes the control-evidence experiments reviewable from one entry
point. It adds a frozen 24-case synthetic comparison, a self-contained K2/K3
offline packet, six controlled LangGraph runtime scenarios and the author-side
validation evidence needed to inspect or rerun them.

The comparison's first holdout run found 16/18 unsupported stronger assertions
for an explicitly naive ACK-promotion rule and 0/18 for the bounded evaluator on
their shared subset. The evaluator recovered 31/31 evidenced claims, while exact
condition agreement remained 52/54. The naive rule is an analytical baseline;
this is not a product or state-of-the-art ranking.

The runtime packet preserves K2 and D/K3 as separate pinned source refs. Its clean
author-side validation checked 172 packet inputs, two isolated runs and 930
archived evidence files. External implementation, reproduction, interoperability
and adoption remain NOT_EVALUATED.

Review starts at `docs/CONTROL_EVIDENCE_RESEARCH.md`. The root README comparison
was also rewritten as repository behavior with explicit evidence limits, avoiding
an unmeasured comparison against a generic “typical framework.”

Validation:

- K1: 44 tests; all 24 cases and 321 comparator rows replayed.
- K5 evidence review: 172 inputs, two runs and 930 archived files verified.
- K5 final packet bytes are unchanged between tested commit `bec6b34` and final
  source candidate `92c17a2`; the later diff is retained reporting evidence.
- Prepublication verifier checks the landing pages, disclosure/approval state,
  impact-ledger boundaries, source ancestry and local links.

These artifacts do not establish third-party validation, production safety,
preemptive cancellation, broad framework superiority, full standards conformance,
same-version external interoperability, adoption or standards-body endorsement.

No release, outreach or standards submission is part of this pull request.
