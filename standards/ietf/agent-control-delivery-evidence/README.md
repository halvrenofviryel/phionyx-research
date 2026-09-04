# draft-abak-agent-control-delivery-evidence — public work area

This directory tracks public work around the individual Internet-Draft
**draft-abak-agent-control-delivery-evidence**, "Evidence Requirements for Agent
Control Delivery and Outcome Reconciliation".

It exists to keep an auditable public record of: the published baseline, the
public reviews received on the IETF SCITT mailing list, the provenance of
externally contributed fixtures, adjacent-domain evidence that was referenced
during review, and the open worklist for a future revision.

## Status

Two states are tracked here and they are **not** the same thing.

- **Current published baseline: `-00`.** Submitted 2026-08-29, posted
  2026-08-31, dated 30 August 2026 in the document itself. The artifacts under
  `draft/published/00/` are the immutable published baseline and the
  authoritative statement of what `-00` says.
- **Current repository candidate: `-01`, dated 3 September 2026.** The author's
  candidate XML, its `-00` → `-01` changelog, and byte-level checksums are
  stored under `draft/candidate/01/`. This is an **author working candidate held
  in this repository**. It is not an IETF artifact and carries no Internet-Draft
  status.
- **`-01` has NOT been submitted to the IETF.** It does not appear on the
  Datatracker, it has not been posted, and it must not be cited or described as
  a published, submitted, adopted, or accepted revision. Where a revision of
  this draft is referenced as published, that revision is `-00`.
- **Review is ongoing.** The public thread is open and no review freeze has been
  declared. The ledger and worklist here are working records, not final
  dispositions. The existence of candidate `-01` text does not close any review
  item and does not convert a reviewer's finding into an agreed outcome.
- **Intended status: Informational** (`category="info"` in the published XML;
  "Intended status: Informational" in the published text).
- On the IETF Datatracker the document is associated with the group
  **"Individual Submissions"**, document state *Active / I-D Exists*.

## What this directory is not

- **This is not evidence of IETF Working Group adoption or of IETF consensus.**
  The document is an individual Internet-Draft. Nothing here has been adopted by
  a working group, and no consensus of any kind is claimed. That applies to the
  `-01` candidate exactly as it applies to `-00`: text the author has written
  into a candidate revision is an **author design decision**, not a WG outcome,
  and not evidence that any reviewer agreed with the resolution chosen.
- **Discussion on the SCITT mailing list does not by itself mean WG adoption.**
  Posting a draft to a list, receiving review, and receiving supportive review
  comments are all distinct from adoption. Reviewer prose in the thread —
  including welcoming or supportive wording — is reviewer opinion and is
  recorded as such.
- **This is not a normative source.** The published `-00` files under
  `draft/published/00/` are the authoritative statement of what `-00` says.
  Everything else in this directory is commentary, provenance, worklist, or
  unpublished candidate text. In particular, `draft/candidate/01/` is **not**
  normative and states nothing about what the Internet-Draft series contains.

## Scope of the draft itself

The draft is **format-neutral**. Per its own abstract, it defines
format-independent evidence requirements and separates issuer-side emission,
receiver-side observation, enforcement outcome, and observation of the resulting
control effect. It states that it **does not define a receipt format, wire
protocol, authorization system, policy language, transparency service, or audit
regime.**

## Relationship to AIREP

The AI Runtime Evidence Protocol (AIREP) is cited in `-00` Section 12
(Implementation Status, marked for removal before RFC publication) as one
experimental implementation source for the distinctions the draft makes. That
section states explicitly that the AIREP artifacts do not establish a deployed
end-to-end delivery or control-effect claim and are cited as implementation and
test-vector input rather than as evidence of broad adoption or IETF consensus.

**This draft is not an effort to standardize AIREP.** AIREP may provide
experimental implementation evidence for the requirements; the draft's
requirements are stated format-independently and do not depend on AIREP.

## Relationship to third-party work

Third-party adjacent work referenced during review — including the EMILIA
Protocol drafts, the contestability work, and the Cedulon audit layer — remains
**third-party work**. It is referenced and attributed here. It is **not**
rebranded as an implementation of this draft, and third-party code is referenced
at a pinned commit rather than vendored. See `RIGHTS_AND_PROVENANCE.md`.

## Layout

```
README.md                     this file
SOURCES.md                    every source consulted, with URL / revision / digest
RIGHTS_AND_PROVENANCE.md      rights and provenance rules for material kept here
draft/published/00/           the immutable published -00 baseline, unmodified,
                              + SHA256SUMS.txt
draft/candidate/01/           current author candidate -01, its changelog, and
                              SHA256SUMS; NOT an IETF-published artifact and not
                              submitted to the Datatracker
reviews/REVIEW_LEDGER.md      one entry per substantive public review item
reviews/DRAFT_01_WORKLIST.md  traceability/review record for -01; records what
                              the candidate implements, not consensus
fixtures/README.md            known contributed fixtures and their provenance
external-evidence/            third-party adjacent-domain evidence, referenced not vendored
```

## Links

- Datatracker:
  <https://datatracker.ietf.org/doc/draft-abak-agent-control-delivery-evidence/>
- IETF `-00` archive (HTML):
  <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-00.html>
- IETF `-00` archive (TXT):
  <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-00.txt>
- IETF `-00` archive (XML):
  <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-00.xml>
- SCITT announcement:
  <https://mailarchive.ietf.org/arch/msg/scitt/UWud7Jg9bN7xHntkH1WPNNn0Dhc/>
- SCITT list archive index:
  <https://mailarchive.ietf.org/arch/browse/scitt/>
