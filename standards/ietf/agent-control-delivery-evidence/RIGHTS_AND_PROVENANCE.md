# Rights and provenance

This directory is a research work area. It holds material with **several
different rights positions**, and copying something here does not change the
rights position it arrived with.

## 1. Published Internet-Draft material

The files under `draft/published/00/` and `draft/published/01/` are the
published Internet-Drafts `draft-abak-agent-control-delivery-evidence-00` and
`-01` exactly as retrieved from the IETF archive. They are unmodified.
`-01` was submitted and posted on 4 September 2026; `-00` remains stored as the
earlier revision.

That material remains subject to the applicable **IETF Trust Legal Provisions
and BCP 78 / BCP 79** terms, as stated in the document itself:

> This document is subject to BCP 78 and the IETF Trust's Legal Provisions
> Relating to IETF Documents (https://trustee.ietf.org/license-info) in effect
> on the date of publication of this document.
>
> Copyright (c) 2026 IETF Trust and the persons identified as the document
> authors. All rights reserved.

Copying that public IETF artifact into this research work area **does not
relicense it under this repository's general software license** (AGPL-3.0, see
`LICENSE` and `LICENSE_STRATEGY.md` at the repository root). The AGPL applies to
this repository's own software; it does not and cannot apply to an IETF
Internet-Draft placed here for provenance.

Do not modify the files under `draft/published/00/` or `draft/published/01/`.
If a future revision is published, add it under a new `draft/published/<NN>/`
directory rather than editing an existing one.

`draft/published/` holds **only** revisions actually published by the IETF. An
author revision that has not been submitted does not go there — see section 7.

## 2. Third-party material generally

Third-party material referenced or stored here **retains its own provenance and
rights**. No licence is asserted, granted, inferred, or invented on behalf of
any third party in this directory. Where a third party has not stated licence
terms, this directory records that fact rather than guessing.

## 3. Cedulon code — referenced, not vendored

The Cedulon `population-probe.mjs` artifact and its README are **referenced at a
pinned commit and are not vendored** into this repository. Only the URL, the
commit, and the independently checked byte/line counts and SHA-256 digest are
recorded, in `external-evidence/CEDULON_POPULATION_PROBE.md`.

At pinned commit `0a3fa04`, the Cedulon repository contains a root
**Apache License 2.0** `LICENSE` file. The probe is referenced rather than
vendored here. This work area does not relicense the probe or assert terms
beyond those stated by the upstream repository.

Verified 2026-09-01 from two independent sources:
<https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/0a3fa04/LICENSE>
(10 848 bytes, SHA-256 `578ddb1a35574604e675c6155ed356ad75b909bae380dcb6d3239081626b2bd8`,
opening "Apache License / Version 2.0, January 2004"), and the npm registry
metadata for `@cedulon/audit@0.8.0`, which declares `"license": "Apache-2.0"`.
No `LICENSE.md`, `LICENSE.txt`, `COPYING`, or `NOTICE` exists at that commit's
root (all HTTP 404).

Anyone wishing to use that code should obtain its terms from the upstream
repository directly.

Cedulon is an **adjacent-domain worked example**. It is not an implementation of
`draft-abak-agent-control-delivery-evidence`, and this directory must not
describe it as one — the probe's own first paragraph and its author's message
both say so explicitly.

## 4. Contributed fixtures

A fixture contributed by an external party must retain **contributor
attribution and provenance** wherever it is stored or used.

For the fixture contributed by Iman Schrock / EMILIA Protocol, the contributor
stated the following provenance rule on the public list
(<https://mailarchive.ietf.org/arch/msg/scitt/5J5i8Y6w3WkzewIzH23oMPpb9cI/>):

- **Unchanged use:** keep the original `fixture_id` and the original SHA-256.
- **Adapted use:** give the derivative a **new ID**, record the **original
  fixture ID and digest as its provenance**, and credit **EMILIA Protocol**.
- The **original contributed fixture stays pinned to AEB `-04`**, even though
  the currently published AEB revision is `-05`. A derivative case, or current
  related-work text, may point to the current AEB revision.

That provenance rule is adopted as the handling rule for this work area. No
licence for the fixture is stated by the contributor and none is invented here;
the fixture is retained under the contributor's stated
attribution-and-provenance conditions.

### Derivative fixtures

Any derivative fixture created later in this work area MUST:

1. receive a **new fixture ID** distinct from the source fixture's ID;
2. record the **source fixture ID and source SHA-256** in its own provenance
   record; and
3. credit the original contributor.

A derivative must never reuse the source fixture's ID or present the source
digest as its own.

## 5. Attribution of review comments

Public mailing-list review comments are quoted only in short, attributed form in
`reviews/REVIEW_LEDGER.md`, with a link to the archived message. Whole messages
are not reproduced here; the IETF mail archive is the record.

Reviewer statements are recorded as **what that reviewer said**, not as
positions of this work area, and not as findings adopted by the draft unless the
author's own public response says so.

## 6. What is not here

No private correspondence and no third-party source code is stored in this
directory. Unpublished draft text is limited to the author's own candidate
revisions under `draft/candidate/`, covered by section 7; no third party's
unpublished draft text is stored here.

## 7. Unpublished author candidate revisions

`draft/candidate/<NN>/` holds the author's own **pre-submission** candidate text
for a revision, together with its changelog and checksums. As of this writing
that is `draft/candidate/01/`.

**`-01` has since been submitted and published** (4 September 2026), and the
published artifacts are under `draft/published/01/`. The candidate directory is
**retained as provenance**: it records the pre-submission digest chain
`da64a038…` → `11884630…` → `98c6ad0d…` → `b7d51500…` → `05a95b59…` and the
review dispositions applied along it, which is the only way the review history
stays checkable. The final candidate digest
`05a95b598c8ebd462ffbcf3ed9a7fedcd08d8555053c8ec57ea43447c3cd64ca` is
byte-identical to the published `-01` XML.

This material has a different position from everything in section 1:

- It is the **author's own pre-submission working text**, not an IETF-published
  artifact. Where it and `draft/published/01/` could ever be read differently,
  the published files control. Earlier candidate states in the chain above were
  never submitted and must not be cited as published, submitted, or adopted
  revisions.
- It carries the usual Internet-Draft boilerplate (`ipr="trust200902"`) because
  it is drafted for eventual submission. The BCP 78 / IETF Trust Legal
  Provisions position described in section 1 attaches to a revision **on
  publication**, not by virtue of being stored here.
- Storing it here does not relicense it under this repository's general software
  licence, for the same reason given in section 1.
- It is **candidate text, not a record of consensus.** Text the author has
  written into a candidate is an author design decision. It is not evidence that
  a reviewer agreed, that a review item is closed, or that any working group has
  adopted anything. `reviews/DRAFT_01_WORKLIST.md` keeps reviewer findings,
  author design decisions, and consensus separate, and records which is which.
- Third-party material summarized or referenced by a candidate keeps the
  provenance and attribution rules in sections 2 to 5. In particular, the
  candidate's summary of the contributed fixture preserves the contributor's
  `fixture_id` and SHA-256 and credits EMILIA Protocol, as section 4 requires.

If and when a candidate is actually published by the IETF, the published
artifacts are added under `draft/published/<NN>/` as section 1 requires. The
candidate directory is not moved, renamed, or retrospectively described as
published.
