# Prepublication review — 3 November 2026

Status: **HISTORICAL PREPUBLICATION SNAPSHOT**. At this snapshot, the candidate
was ready for owner review, no publication permission had yet been granted, and no
push, pull request, issue, release, external message or standards submission had
been performed. The owner later approved this exact unit and its disclosures for
a public branch and draft PR. That approval produced
[PR #108](https://github.com/halvrenofviryel/phionyx-research/pull/108); it did not
authorize merge, release, outreach or standards submission.

## Recommended first publication unit

The first unit combines the bounded K1 comparison with the K2/D/K3 self-service
packet and the author-side K5 validation. The runtime packet is the primary entry;
K1 is supporting research. The root README and Standards Lab point to one bounded
landing page instead of presenting each internal task code as a separate headline.

Included source heads before integration:

- K1 `a7afc505ece2948966b510aefe595f13403c0232` based on public
  `652e008d18805a1c69492a688e621df91f143287`.
- K5 `92c17a237bcc73c3ac69dbb879e1f358c705a739`, containing K2
  `ea1f39a6da72639a73e601918a6c8bc87bff1d77`, K3
  `76ecce0b378a6b391850795abf45fb6aca8e1d6b` and D base
  `0130fcf8e7d70a0f9c4f977957e5de76ca8ef689` in its source bundle.
- K5's tested packet commit is
  `bec6b34c55d5a1f3e898997475539c9d54c91580`. The final source/runner/dependency
  packet is byte-identical through `92c17a2`; the later commit adds reports and
  retained validation evidence.

## Deliberate exclusions

- B2/B3 and the earlier pilot remain a separate publication unit because their
  full reveal and run metadata require their own explicit scope decision.
- H2 CP-01 remains a separate repository candidate. Publishing a repository copy
  would not authorize IETF submission.
- F and K4 are not included. No SCITT/COSE verification claim is added.
- No outreach text, issue comment, email, release or website announcement is included.

## Disclosures that approval must cover

- K1 publishes all 24 synthetic cases, latent truths, oracles, original development
  iterations and the first holdout output, including both condition differences.
- K1 includes a clearly named synthetic Ed25519 private key fixture in the author
  bundle. It is intentionally public test material and has no real authority.
- K5 distributes the previously unpublished K2 and D/K3 source histories inside
  `airep-sources.bundle`, plus pinned dependency archives and their licenses.
- Frozen logs retain development paths, timestamps, process and namespace metadata.
- The package is about 41 MiB across the K1 and K5 directories before Git packing.

## Claim decision

Allowed headline: a self-contained control-evidence research packet with a
frozen synthetic comparison and six controlled LangGraph runtime scenarios.

Disallowed headlines include: industry-leading benchmark, third-party-validated
system, production-safe cancellation, full ACDER/AIREP conformance, independent
same-version interoperability, adopted standard or IETF-endorsed work.

External results from Emek Can Doğru and Joel Hillier/Certisyn remain separately
credited, version-bounded evidence. They are not validators of this new package.

## Gate disposition

At this snapshot, public push and PR creation required explicit owner approval of
the exact combined unit and the disclosures above. That bounded approval was later
granted and consumed for the public branch and draft PR #108. PR merge, release,
outreach and any IETF submission remain separate later decisions.
