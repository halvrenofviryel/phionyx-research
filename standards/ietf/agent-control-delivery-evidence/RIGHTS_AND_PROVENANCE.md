# Rights and provenance

This directory is a research work area. It holds material with **several
different rights positions**, and copying something here does not change the
rights position it arrived with.

## 1. Published Internet-Draft material

The files under `draft/published/00/` are the published Internet-Draft
`draft-abak-agent-control-delivery-evidence-00` exactly as retrieved from the
IETF archive. They are unmodified.

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

Do not modify the files under `draft/published/00/`. If a future revision is
published, add it under a new `draft/published/<NN>/` directory rather than
editing the existing one.

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

No private correspondence, no unpublished draft text, and no third-party source
code is stored in this directory.
