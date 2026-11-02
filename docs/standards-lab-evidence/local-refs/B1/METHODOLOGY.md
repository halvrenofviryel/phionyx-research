# Method and boundaries

B1 builds an original sealed challenge for the exact published
[draft-abak-agent-control-delivery-evidence-02](https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-02.txt).
Its only repository base is `69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d` on
`codex/acder02-sealed-challenge-builder`. Initial status was clean. Fetch succeeded
and did not change HEAD. The read-only check of origin/main found that same base.
The stale origin/HEAD symbolic reference was left untouched. The machine-readable
`public/source_audit.json` gives acquisition times, exact revision URLs, raw-byte
SHA-256 values, byte lengths, latest-revision difference and fetch observations.
The Datatracker response independently reported revision 02; the frozen baseline
was never silently upgraded. Raw draft text is preserved byte-for-byte, including
its notices and formatting; no draft text or normative AIREP schema was edited.

## Prior work review and original case construction

Only the current proofbundle `interop/acde_01` README and RUN_RECORD were read,
at head `c8b5b28519191cbe8d229cbf3378e749cb8ccc64` and independently fetched at the
-02 draft's historical pin `19c3b0b909639d2b6e4cfff04d9434c878be3616`.
Both files were identical across those revisions. This establishes the scoped
source comparison, not that the entire repositories are identical. The reported
146-vector run and 14 ambiguity findings remain historical author reports from
that source; B1 did not rerun them. No implementation, vector generator or vector
file was read or copied. Sources are identified and hashed, not vendored into
the solver export. The new records use an independently authored descriptive
representation with literal inputs, no inherited merge-patch vectors.

Section 14 and the operative -02 clauses were read together. The resulting
coverage map identifies themes, not expected per-case outcomes:

| Cases | -02 clarification or retained requirement | Draft sections |
|---|---|---|
| 01 | Unclosed target accounting, no invented obligation | 4.2, 5.11, 6.4 |
| 02, 08 | Terminal empty versus all-excluded populations, parent semantics | 5.11, 6.2, 6.4–6.5 |
| 03, 13 | Correlation, record partitioning and receipt semantics | 4.3, 5.11, 6.1, 6.4 |
| 04 | Missing issuer evidence while receiver facts remain available | 5.4, 6.5 |
| 05 | Same-scope issuer content reuse | 5.10, 6.1 |
| 06 | Target-specific delivery and parent scope | 4.2, 5.5, 6.2 |
| 07 | Bounded deadline observations | 5.8, 9.1 |
| 08, 09 | Frozen permitted exclusion inputs and separate accounting | 4.2, 5.11, 6.5 |
| 10 | Ordering basis; admission, entry and later activation | 5.9, 9.4 |
| 11 | Separate enforcement/effect namespaces | 4.4–4.5, 5.6–5.7 |
| 12 | Structural result, attribution and coverage qualification | 5.3, 5.13, 5.15, 6.5–6.6 |
| 13 | Intermediary loss and a record without endpoint-read semantics | 4.3, 5.16 |
| 14 | Frozen positive aggregate failure conditions, two profile choices | 5.10, 6.5 |

The profile-dependent case is run twice under already public policies. This
records an actual draft-permitted degree of freedom instead of inventing one
universal answer. Pre-boundary failure scoping, full retry reduction, all native
verification paths and the implicit default claim are not exhaustively exercised.
This is a 14-case targeted experiment, not the draft's complete conformance suite.

## Seal and verification

The complete expected-results envelope uses a fresh cryptographic 256-bit nonce.
A plain hash of the small result space would permit enumeration; that is not the
scheme used here. The exact serialization, allowed Unicode/numbers, envelope
fields and domain version are in `public/PUBLIC_CHALLENGE.md`. The public input
inventory and output contract are bound through the canonical manifest digest.
The full envelope SHA-256 and byte length are public; no nonce, nonce digest or
unsalted answer digest is published. Initial sealing is randomized; all checks
of the frozen package are deterministic. Length leakage is acknowledged.

The private results are generated from an author-side interpretation of the
pinned text and frozen profile and stored only in the reveal outside this clone.
The private derivation is not a solver and is not evidence of an independent
implementation. A future mismatch must be reviewed against source clauses and
profile declarations; the author's seal commits an interpretation, not truth.
Tool tests use synthetic results unrelated to the challenge, mutate one answer
byte and nonce byte, exercise rejected canonical domains, tampered public inputs,
context mismatch, overwrite protection and private-path controls. Public tests
check case structure, the complete public inventory and committed HEAD bytes.
An owner-only audit checks the real reveal and searches the entire working clone
(excluding Git's object database) for nonce encodings, whole envelope/results
and per-run answer objects. It also checks public JSON input allowlists and
reviews docs and filenames for per-case expected-value hints. This is a practical
leak check, not proof against arbitrary covert encoding or semantic inference
from intentionally informative inputs. No actual answer values are printed.

## Access boundary and claims

The reveal and derivation reside under the owner's standards-private B1
directory, outside the clone and public export. Its directory is mode 0700 and
files are 0600. These permissions restrict other UNIX users; they do **not**
restrict another agent running as the same UID. Git exclusion and a hidden path
would not establish blindness either. Do not send this author task's history,
private derivation, reveal or repository checkout to a future solver.

**B2 was not created or run.** B2 may begin only after a separate environment is
verified unable to access the private directory and author context, with only a
hash-verified public export supplied. The coordinator must capture the original
commitment before implementation, then freeze solver code and outputs before
reveal. This gate is a future requirement, not a task launch or schedule.

Even such a run under the same user's control is expectation-blind
second-implementation evidence, not third-party independent evidence. Stronger
external evidence requires a genuinely external implementer and separately
controlled provenance. Cryptographic signatures are not event truth; supplied
records are not the full deployment population; balanced counts are not complete
mediation; an unknown never becomes PASS or FAIL merely to complete a table.
The input native-valid flags are synthetic premises, not actual signatures.
AIREP is not the conformance authority and its frozen v0.1 content is untouched.
Only local public files, tooling and this scoped documentation are committed.
No push, PR, issue, publication, email, external comment or IETF submission occurs.
