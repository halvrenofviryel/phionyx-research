# Roles and independence

Choose the narrowest class supported by attributable evidence. All entries in
this candidate packet are author-controlled; no external run is being asserted.

| Class | Meaning | What does not establish it |
|---|---|---|
| AUTHOR_SIDE_REFERENCE | Author's implementation and regression/replay | Different language, process, key or repository is not another author |
| AUTHOR_CONTROLLED_BLIND_SECOND | Same owner controls a separate implementation made without expected answers | A plain separate checkout is insufficient isolation; no such new run is made by K5 |
| EXTERNAL_PRODUCER_ONLY | An attributable outside producer supplies pinned artifacts | A template or local test double is not a submission |
| EXTERNAL_CONSUMER_ONLY | An attributable outside consumer evaluates pinned inputs using disclosed logic | Reference-code reuse must be disclosed and does not establish independent implementation |
| EXTERNAL_SAME_VERSION_CROSS_INTEROP | Required outside producer/consumer roles actually exchange the same exact protocol revision | Older v0.1.2 and v0.2 evidence cannot be added together |
| EXTERNAL_REPRODUCTION | An attributable outside party reruns the author's code | This is not independently authored protocol logic |
| EXTERNAL_PRODUCT_INTEGRATION | An external controlled product actually integrates the code, with attributable deployment/run evidence | A demonstration, citation, or declared interest is not adoption |
| CITATION_ONLY | Verifiable citation or acknowledgement | No implementation, execution, or adoption follows |
| NOT_EVALUATED | Required evidence is absent or unassessed | Not a negative fact about what someone did |

Before accepting an external report, establish:

- Maintainer identity, repository/project control, public source and permission to cite.
- Exact source commit/release, protocol revision, relevant schema/source hashes,
  dependencies, OS/toolchain, license, and test-key ownership.
- Confirmed role: producer, consumer, verifier, rerunner, or product integrator.
- How the implementation was written; any copied/reference logic; whether expected
  outputs were seen; any blind/reveal procedure and its technical isolation.
- Exact command, native result, stdout/stderr, input/output hashes, failures,
  uncertainty, missing observations, scope limits, and data-redaction notes.
- Separate maintainer-side reproduction and the external project's acceptance
  status. A received report is not automatically accepted or an endorsement.

Native AIREP observer independence, software authorship independence, organizational
control and production adoption are distinct. K2's demo observer policy is
stipulated. K3 declares same_executor and writable control authority. Neither
supplies an independent witness. All external classification remains
NOT_EVALUATED until a real submission and review exist.
