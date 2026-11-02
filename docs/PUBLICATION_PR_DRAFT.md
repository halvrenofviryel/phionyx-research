# Local PR draft — not submitted

Repository: `halvrenofviryel/phionyx-research`.
Proposed base: `main`, observed public base `69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d`.
Local source branch: `codex/standards-lab-publication-candidate`.
Exact content commit and parent chain: `publication_review.json`, U1.
`approval_granted=false`; no remote branch or PR created.

## Exact title

Add bounded standards experiments and a reproducible Standards Lab

## Exact multiline body

The repository lacked a single reproducible inventory of its standards experiments,
and some README descriptions overstated AIREP version and signing behavior. This
change adds a Standards Lab with exact source revisions, commits, hashes, commands
and limits, and aligns the root README and portfolio format identifiers.

The publication scope is S0/A/C03/C04/E plus the Lab. C03 remains frozen to -03.
The separate -04 addendum reproduces F1/F2/F4 rejecting and the other seven vectors
being accepted by the released CLI; it does not execute the full draft procedure.
F10 consumption is NOT_EVALUATED and no runtime execution/effect is observed.
D/F are attributed report references; H1 records a scoped NO-GO, and H2 remains a
separate unpublished informative candidate. B2/B3 are pending.

Validation:

- Original A/C03/E replay: 59 + 16 + 30 tests passed; these suites were not rerun
  for the documentation update.
- Added C04 replay: 13 tests passed and 33 outputs matched byte-for-byte without
  normalization; all 55 imported files and 123 frozen S0/A/C03/E files preserved.
- Index, source/run hashes, links, local claim lint, and default U1 review checks
  pass. Authored whitespace is clean; raw source formatting is preserved.

These internal results do not establish third-party validation, full conformance,
adoption, event truth or population completeness. Outreach commits, D/F application
code and H2 candidate files are excluded from this branch and its ancestry.
