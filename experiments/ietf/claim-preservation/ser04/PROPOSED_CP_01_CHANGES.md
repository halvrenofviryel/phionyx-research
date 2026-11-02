# Conditional editorial preparation for a possible CP-01

**UNSUBMITTED / NON-NORMATIVE / CONDITIONAL.** These are review notes, not a draft
revision, adoption proposal or new normative requirements. Published CP-00 remains
unchanged. No endorsement by Gruszka, Watts, proofbundle, SCITT or the IETF is claimed.

## Possible Implementation and Validation Status addition

Condition: the author reviews this profile, verifies the result commit and accepts
the stated limits. The following informative text could then be considered:

> A local same-author experiment, profile `cp-ser04-local/1`, examines bounded
> claim distinctions in Signed Evaluation Receipts -04 and Evaluation Receipt
> Mappings -04. It executes direct receipt consumption, the payload-carrying DSSE
> mapping and typed digest references with and without supplied receipt bytes.
> It covers all twenty Appendix A scenarios as local probes, including explicit
> native-domain boundary refusals, and reports a twelve-requirement matrix.
> The experiment does not establish full CP or SER conformance, Ed25519/SCITT
> verification, independent interoperability, real-model evaluation, complete
> population coverage or arbitrary semantic preservation. Its internal normalized
> records are not proposed wire formats.

If counts are included, use the committed measured reports: 30 unit tests,
80 scenario-route observations, 48 bounded matrix cells. The latter classify
17 PRESERVED, 10 QUALIFIED_LOSS, 17 UNESTABLISHED and 4 NOT_APPLICABLE. The scenario
counts are different (34, 17, 13 and 16 respectively); do not conflate the units or
present 17/48 as a conformance score. Test/check counts are implementation evidence,
not evidence that an evaluation event occurred.

## Possible informative mapping-profile reference

Condition: a stable, accessible reference has been chosen by the author. Until then,
the concrete **local** reference is repository directory
`experiments/ietf/claim-preservation/ser04/`, with profile `mapping_profile.json`,
source ledger `SOURCE_PINS.json`, observations `results.json` and results `RESULTS.md`
in the result commit containing these files. This work has not been pushed, so no
public commit URL or adopted implementation reference is asserted. A future citation
should pin that commit, the profile digest and the original draft revisions, rather
than a moving branch. Source retrieval times and hashes must remain attached.

## Clarifications supported by the measurements

These would explain existing R-CP clauses, not add obligations to accommodate this
implementation:

1. **Native representability and bounded claims (4.3, 4.12, Appendix A).** A format
   that necessarily carries a criterion comparison cannot supply a no-criterion
   completed-run example without changing its domain. Explicitly report a refused
   mapping or native-domain boundary case. CP-T01/02/05 remain NOT_APPLICABLE as
   native SER positive examples; R-CP-3's requested state distinctions remain
   UNESTABLISHED for this carrier. Do not count refusal as complete preservation.
2. **Digest resolution versus historical carriage (4.8–4.10).** A digest-only
   reference with no candidate supplies no score. A matching candidate restores
   access to its B bytes, but does not recover a qualification absent before B,
   authenticate its key or prove its assertions. CP-T11/12 and mappings C5/R7
   concretely distinguish reported digest, matched bytes, reference form and
   semantic support. Local reference resolution must not be called a SCITT
   registration or Ed25519 verification result.
3. **Numerical derivation (4.4).** CP-T08 uses public P2: score `0.762`, comparator
   `>=`, threshold `0.800`, source `passed=false`. One-decimal rounding yields
   `0.8`, whose presentation comparison is true. The exact source comparison,
   rounded derivation and any later policy judgment need separate attribution;
   these are already required by CP-00.
4. **Coverage and provenance limits (4.1, 4.6, 4.9).** A reported `n` and all
   supplied records do not establish the full population or all actual attempts.
   CP-T07/12/16 expose absent retry, exclusion and amendment information. A local
   source/output binding detects substituted local records (CP-T18) but does not
   mean the native receipt acquired a mapping-instance field or that a loss
   inventory is authenticated or complete.

## Conditions not established here

No additional independent producer/consumer was run. Reconstruction of external
proofbundle fixture bytes is not execution of proofbundle or an independent
interoperability result. Ed25519, COSE and SCITT verification were not executed;
the later-authentication probe is a local symmetric test MAC. EQR-05 is context
only. Exact executed identity, evaluator independence, pre-run criteria chronology,
full sample populations and source truth remain unknown. No normative change or
IETF submission follows automatically from these notes.
