# A Score Is Not a Verdict: Why AI Evaluation Evidence Needs Claim Preservation

*A new IETF Internet-Draft proposes format-neutral rules for keeping run state,
metric identity, criteria, coverage and uncertainty intact as evaluation
results move between tools.*

AI evaluation results rarely stay where they were created. A harness writes a
run log. An adapter normalizes it. An evidence service signs an export. A
dashboard selects one number. A downstream team uses that number in a release
decision. At each step, the representation can become cleaner while the claim
becomes less faithful to the original evidence.

That is the problem addressed by the new individual Internet-Draft,
[Claim-Preserving Exchange of AI Evaluation Evidence](https://datatracker.ietf.org/doc/draft-abak-ai-evaluation-claim-preservation/).
It proposes twelve format-neutral preservation requirements and twenty mapping
test scenarios for checking whether the meaning, scope and material
qualifications of evaluation evidence survive transformation.

The premise is simple: preserving a score is not the same as preserving what
the score supports.

## Run completion is not metric success

Consider an evaluation job that exits normally. The scheduler marks the run
`completed`, the result file exists, and the exporter returns success. None of
those facts establishes that a particular metric met its criterion.

The metric may have failed. It may have been skipped. Its computation may have
errored after other checks completed. The run may have finished without the
required measurement executing at all. If an adapter maps every completed run
to a green evaluation result, it has changed a statement about process state
into a statement about measured performance.

Claim preservation therefore keeps execution state separate from measurement
state and from the criterion judgment. `COMPLETED`, `PASS`, `NOT_MEASURED` and
`ERROR` answer different questions. A downstream system can still apply a
conservative policy to missing evidence, but it should not rewrite missing
measurement as observed failure—or, worse, as success.

## One run is not one metric

Modern evaluation runs often contain multiple tasks, metrics, slices and
aggregations. A single run identifier may hold accuracy, refusal behavior,
latency, subgroup results and several variants of the same score.

Selecting “the score” without preserving the result identity creates an
unstated choice. Was the value a macro average or a micro average? A primary
metric or a diagnostic? A final result or an intermediate computation? If an
exporter serializes one numeric value while dropping the selector that chose
it, a later reader cannot tell which result the number represents.

The draft treats result selection as evidence. A mapped claim needs a stable
way to identify the source result and its relationship to the run. That does
not require a universal metric vocabulary. It requires the transformation to
retain enough source meaning that a consumer can distinguish the selected
result from its neighbors.

## Partial coverage is not complete evaluation

A campaign can contain valid local PASS results and still fail to establish a
population-wide conclusion. Suppose a suite expects ten model versions, five
languages and three deployment configurations. Every supplied row may be
internally consistent, yet the package may cover only a subset of that intended
population.

This is a denominator problem. Counting the records that arrived does not prove
that the record set is complete. An export should preserve both the observed
population and the basis—if any—for claiming that the population is complete.
If completeness is unresolved, the honest result can be “all supplied cases
passed; campaign-wide coverage not established.” That is more useful than
collapsing everything into either a naked green badge or an undifferentiated
unknown.

## Rounding can change a threshold judgment

A score of `0.9496` may display as `0.95`. If the criterion is “at least 0.95,”
the displayed value appears to pass while the source value fails. The inverse
can happen around strict inequalities or when different decimal and binary
representations are compared.

The issue is not that rounding is forbidden. Reports need readable numbers.
The requirement is that a representation change must not silently change the
criterion judgment. A mapping should preserve the source value or its exact
reference, the rounding or normalization rule, the comparator, the threshold,
and whether the judgment was made before or after transformation. Otherwise a
cosmetic formatting choice becomes an unrecorded decision rule.

## Authentication is not preserved semantics

A signed export can be byte-authentic and still be semantically misleading. A
signature can bind a payload to a key accepted by a verifier. It does not prove
that the selected score was the intended metric, that a skipped check ran, that
the covered population was complete, or that caveats survived an adapter.

This is why cryptographic protection and claim preservation belong on separate
axes. Signing a lossy summary makes later alteration detectable; it does not
restore the distinctions already discarded before signing. RATS, SCITT,
in-toto and related mechanisms provide important building blocks for
attestation, registration and supply-chain integrity. The new draft does not
replace them. It asks what an AI evaluation mapping must keep intact when using
or composing with such mechanisms.

## A format-neutral review discipline

The draft deliberately does not define a new wire format, benchmark, frontier
threshold, evaluator certification, safety certification, authorization
protocol or cryptographic envelope. Its requirements can be applied to JSON,
tables, evidence graphs, signed statements or report-generation pipelines.

The twenty scenarios are likewise not reported interoperability results. They
are mapping tests: small cases designed to expose whether a transformation
preserves distinctions such as missing measurement, metric multiplicity,
coverage limits, threshold precision and downstream inference. Passing them
would support only the tested mapping behavior, not certify a model or an
evaluation organization.

This work grew from the argument in
[Access Is Not Yet Verifiability](https://huggingface.co/blog/phionyx/access-is-not-yet-verifiability):
valid records and evaluator access are necessary, but a later consumer can
still expand a bounded observation into an unsupported verdict. The draft turns
one part of that argument into reviewable requirements and counterexample-ready
scenarios.

AIREP's Embedded Evaluation Profile 0.1 appears only as informative related
work. It offers one experimental place where some evaluation-evidence
distinctions can be represented. The Internet-Draft is broader, does not depend
on AIREP, and does not revise AIREP conformance or maturity.

The practical invitation is straightforward: take a real evaluation export,
map it into another tool, and ask whether a skeptical reader can still tell
what ran, which result was selected, what criterion applied, what population
was covered, what evidence was unavailable, and which later judgments came
from a downstream consumer. If any of those answers disappear, the score may
have survived while the claim did not.

This is an individual Informational Internet-Draft. It is not WG-adopted, not
IETF consensus, and not an IETF-endorsed standard. Publication is not evidence
of implementation or interoperability.

