# CP-00 requirements and scenario derivation

NON-NORMATIVE reading notes. Authority is the newly fetched published CP-00 text, not AIREP or local implementation behavior. No new requirements are introduced.

CP-00 SHA-256: `9088079da04ed23fdead8a54894ac70bcf6ff26ce4834c815e4dc6961986de54`.

| Requirement | Published section/title | Derived obligation | Probes |
|---|---|---|---|
| R-CP-1 | 4.1 Source and Mapping Identity | Identify source snapshots, selectors, interpretation rules, converter and profile; bind material mapping information to the actual source and output. Distinguish digest byte selections. | CP-T18 |
| R-CP-2 | 4.2 Unambiguous Result Selection | Select a unique result and its task/metric/attempt/population context under a declared syntax. Do not resolve ambiguity by choosing a favorable record. | CP-T04, CP-T19 |
| R-CP-3 | 4.3 Execution, Observation, and Assessment | Keep execution, observation and criterion assessment distinct. Omitted criterion information is not explicit absence; missing/error/invalid/non-execution is neither measured success nor failure. | CP-T01, CP-T02, CP-T05 |
| R-CP-4 | 4.4 Values, Units, and Numerical Transformations | Preserve exact numeric meaning, units and uncertainty when supplied. Mark rounding and other transformations; a rounded display cannot establish the original threshold comparison. | CP-T08 |
| R-CP-5 | 4.5 Criteria, New Judgments, and Chronology | Attribute source criteria and later judgments separately. Chronology needs supporting evidence; timestamps and digest commitments alone do not establish pre-run criteria. | CP-T03, CP-T15 |
| R-CP-6 | 4.6 Coverage, Aggregation, and Attempts | Keep population accounting, missing portions, retries and aggregation rules. Supplied records do not establish the full set of actual attempts. | CP-T06, CP-T07 |
| R-CP-7 | 4.7 Qualified Identity and Evaluation Context | Distinguish declared names and commitments from verified executed identities and context. Carry the strength, scope and verification basis of evidence. | CP-T09 |
| R-CP-8 | 4.8 Evidence Availability and Digest Knowledge | Distinguish actor-scoped availability from reported, recomputed or unavailable digests. Do not fabricate bytes, custody, reasons or existence. | CP-T10, CP-T11 |
| R-CP-9 | 4.9 Loss, Conflict, and Multi-Hop Preservation | Track copied assertions, derivations, conflicts and losses across hops. Later authentication cannot recover discarded qualifications or certify a complete loss inventory. | CP-T12, CP-T16 |
| R-CP-10 | 4.10 Typed Verification and Bounded Consumption | Type verification by actor/procedure/inputs and keep structural, digest, signature and substantive checks distinct. Bound processing and keep unsupported claims unestablished. | CP-T13, CP-T20 |
| R-CP-11 | 4.11 Separate Reliance and Downstream Decisions | Do not invent a governance/control event from export. Actual reliance records need separate attribution, policy, subjects and inputs; they alone establish neither authority nor effect. | CP-T14 |
| R-CP-12 | 4.12 Versioned Mappings and Verification Evidence | Version supported semantics and unknown-value policy; report concrete negative/ambiguous fixtures and observed behavior. Same-author testing is not independent interoperability. | CP-T17 |

These paraphrases do not replace the published normative clauses. The matrix labels apply to explicitly bounded questions, not a claim that a whole R-CP requirement is satisfied.

| Scenario | Published section | Executable obligation |
|---|---|---|
| CP-T01 | Appendix A.1 | Run completion and a score cannot be turned into a source criterion verdict. |
| CP-T02 | Appendix A.2 | Explicit absence and unavailable criterion information stay distinct. |
| CP-T03 | Appendix A.3 | A later threshold assessment has its own actor, rule, inputs and result. |
| CP-T04 | Appendix A.4 | No first/last/favorable selection without a unique snapshot selector. |
| CP-T05 | Appendix A.5 | Local source states are retained but unsupported by SER; no boolean coercion. |
| CP-T06 | Appendix A.6 | Reported n does not supply a campaign denominator. |
| CP-T07 | Appendix A.7 | Known attempt/deduplication context is not transported by SER. |
| CP-T08 | Appendix A.8 | The exact P2 score remains false while its rounded presentation compares true. |
| CP-T09 | Appendix A.9 | Declared suite/model/dataset commitments do not establish executed artifacts. |
| CP-T10 | Appendix A.10 | The offline observer has neither bytes nor digest; no invented custody/existence. |
| CP-T11 | Appendix A.11 | criteria_digest is an issuer report, not recomputation of unseen criteria bytes. |
| CP-T12 | Appendix A.12 | A later test MAC authenticates only the surviving bytes; lost coverage stays lost. |
| CP-T13 | Appendix A.13 | Local MAC authentication is separate from unsupported payload interpretation. |
| CP-T14 | Appendix A.14 | No decision/control/release event is invented. |
| CP-T15 | Appendix A.15 | P10 criteria digest and timestamp do not establish pre-run ordering. |
| CP-T16 | Appendix A.16 | Two snapshots remain distinct; SER has no amendment link to transport. |
| CP-T17 | Appendix A.17 | Unknown local profile and native payload basis cannot reuse old semantics. |
| CP-T18 | Appendix A.18 | Local record must match source, output and selector; no native wire binding claimed. |
| CP-T19 | Appendix A.19 | Reject duplicate decoded names deterministically. |
| CP-T20 | Appendix A.20 | Retain common source and both later judgments without rewriting it. |

CP-T01, CP-T02 and CP-T05 are native-domain boundary probes: valid SER requires a criterion comparison and has no execution-state enum. Their local context records are not invented SER extensions. CP-T10, CP-T12 and CP-T16 also use explicitly marked local context, never claimed to have survived in the carrier.

SER-04 section 3.2 supplies suite, suite_version, metric, comparator, threshold, score, passed, n, commitments, timestamp and optional criteria_digest. Sections 3.3, 3.5 and 6 bound their meaning. Mappings-04 sections 3.1–3.3 fix B identity; section 4.1 carries B in DSSE; section 5.1 carries only its digest; section 8 explicitly disclaims complete coverage and mapping-instance records.
