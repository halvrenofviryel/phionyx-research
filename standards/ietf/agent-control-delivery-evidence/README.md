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

- **Current published baseline: `-01`.** Submitted and posted 2026-09-04,
  dated 4 September 2026 in the document itself, 46 pages. The artifacts under
  `draft/published/01/` are retrieved unmodified from the IETF archive and are
  the authoritative statement of what `-01` says.
- **Previous published revision: `-00`.** Submitted 2026-08-29, posted
  2026-08-31, dated 30 August 2026. It remains stored unmodified under
  `draft/published/00/` as the immutable earlier baseline. It is superseded as
  the current revision, not withdrawn or corrected.
- **`draft/candidate/01/` is retained as provenance, not as the draft.** It
  holds the author's pre-submission working candidate, its `-00` → `-01`
  changelog, and the byte-level digest chain that led to the submitted bytes. It
  is **not** the authoritative statement of what `-01` says — `draft/published/01/`
  is. The candidate directory is kept because the review and disposition history
  is only checkable against it.
- **The submitted bytes are byte-identical to the final candidate.** The
  published XML digest
  `05a95b598c8ebd462ffbcf3ed9a7fedcd08d8555053c8ec57ea43447c3cd64ca` equals the
  final candidate digest recorded in `draft/candidate/01/SHA256SUMS.txt`, so the
  candidate-to-published transition introduced no change.
- **Review is ongoing.** The focused pre-submission review round is closed and
  its dispositions are recorded, but the public thread remains open and no
  review freeze has been declared. The ledger and worklist here are working
  records. Publication of `-01` is **not** evidence that a reviewer agreed with
  any resolution chosen.
- **Intended status: Informational** (`category="info"` in the published XML;
  "Intended status: Informational" in the published text).
- On the IETF Datatracker the document is associated with the group
  **"Individual Submissions"**, document state *Active / I-D Exists*. As of the
  `-01` posting the Datatracker record carries **no stream assignment**, which is
  why the submitted RFCXML deliberately omits `submissionType`.

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
- **This is not a normative source.** The published files under
  `draft/published/01/` and `draft/published/00/` are the authoritative
  statement of what those revisions say. Everything else in this directory is
  commentary, provenance, worklist, or pre-submission candidate text. In
  particular, `draft/candidate/01/` is **not** normative: it is retained to make
  the review and disposition history checkable, and where it and
  `draft/published/01/` could ever be read differently, the published files
  control.

## Scope of the draft itself

The draft is **format-neutral**. Per its own abstract, it defines
format-independent evidence requirements and separates issuer-side emission,
receiver-side observation, enforcement outcome, and observation of the resulting
control effect. It states that it **does not define a receipt format, wire
protocol, authorization system, policy language, transparency service, or audit
regime.**

## Relationship to AIREP

The AI Runtime Evidence Protocol (AIREP) is cited in Section 12
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
draft/published/00/           the immutable published -00 revision, unmodified,
                              + SHA256SUMS.txt
draft/published/01/           the current published -01 baseline as retrieved
                              from the IETF archive, unmodified (XML/TXT/HTML)
                              + SHA256SUMS.txt
draft/candidate/01/           the author's pre-submission candidate for -01, its
                              changelog and digest chain; retained as provenance.
                              Superseded as the authoritative text by
                              draft/published/01/
reviews/REVIEW_LEDGER.md      one entry per substantive public review item
reviews/DRAFT_01_WORKLIST.md  traceability/review record for -01; records what
                              the candidate implements, not consensus
fixtures/README.md            known contributed fixtures and their provenance
external-evidence/            third-party adjacent-domain evidence, referenced not vendored
```

## Links

- Datatracker:
  <https://datatracker.ietf.org/doc/draft-abak-agent-control-delivery-evidence/>
- IETF `-01` archive (HTML):
  <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-01.html>
- IETF `-01` archive (TXT):
  <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-01.txt>
- IETF `-01` archive (XML):
  <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-01.xml>
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
