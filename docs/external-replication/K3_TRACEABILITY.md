# K3 event → artifact → bounded claim

This table describes the frozen D + K3 adapter, without extending AIREP's
semantics. Per-run `event-mapping.json` and hashed `evidence[]` pointers provide
the actual event IDs and bytes; this table describes the mapping rule.

| Raw event or observation | Produced artifact/field | Supported bounded statement | Open claim and why |
|---|---|---|---|
| `decision_recorded`, `control_command_produced` | Decision input/output hashes, local authorization assertion; produced command alone creates no successful Control dispatch | The local operator authored a stop request and exact command bytes | Correct/independent authority is not established; test policy is stipulated and authority is writable by the controlled system |
| Successful Pipe `send_bytes`, `issuer_dispatched` | Control `control_event=dispatched`, `boundary_side=issuer`, instruction/action digests | The issuer's local send returned successfully | Receiver receipt, enforcement, execution and effect do not follow from send success |
| Actual `BrokenPipeError`, `delivery_failed` | Control `delivery_failed`; no successful dispatched/received or stop Execution invented | The selected closed local channel failed this send | Remote reachability and other delivery paths are untested; missing receipt is not universal non-delivery proof |
| Actual `recv_bytes`, `receiver_observed` | Control `received`, `boundary_side=receiver`, digest of received bytes | This receiver read the matching command | Receipt is not enforcement; the disabled-handler negative control receives it and continues four steps |
| `enforcement_requested` only | Source event retained; no successful Execution from request alone | Cooperative pause was requested at the instrumented boundary | A callback/request does not prove native runtime pause |
| Matching receipt/request plus native `GraphOutput.interrupts` and checkpoint interrupt/next-node data | Execution `executed`, action/instruction digests and event evidence pointers | Actual LangGraph cooperative pause was observed at this node boundary | D's reconciler has no native enforcement predicate, so `enforcement_observed` stays null + NOT_EVALUATED; no preemptive/terminal cancellation guarantee |
| `enforcement_unavailable` in disabled handler | Execution `failed`, actual no-pause action digest; native TOCTOU mismatch retained | The chosen handler could not apply the requested pause | Receipt and file activity cannot upgrade this failed stop into successful enforcement |
| `business_step_written`, actual fsync-backed file bytes, `graph_completed` | Raw runtime events/effect file; these are business operations, separate from the stop Execution artifact | Four baseline steps or the one completed step can be inspected | AIREP stop Execution is not a blanket statement about all business actions or history |
| Actual two-read post-run `effect_observed`, with a bound stop Execution | Effect `observed_state`, state digest, `observer_relationship=same_executor` | The selected local file state was sampled in the recorded window | No independent corroboration, causal effect proof, future stability or full target coverage follows |
| Native pause but `observation_disabled` | Execution retained; no Effect emitted; effect evidence MISSING | The runtime pause was captured without a post-run effect observation | Effect remains unknown; native pause is not a substitute for the missing observer |
| Worker exit/join or timeout cleanup | Cleanup event/log; forced termination is never emitted as stop-success evidence | Local process cleanup status is recorded | Timeout cleanup is not a tested control enforcement guarantee |

In the complete local pause scenario, **0 or 1 measured business steps** supports
the controlled scheduling observation. `enforcement_observed` nevertheless stays
NOT_EVALUATED because D deliberately does not implement a separate enforcement
adjudication predicate. `relying_party_claim_support` also stays NOT_EVALUATED:
no consumer-specific claim/acceptance policy is evaluated. This is a deliberate
boundary between runtime measurements and stronger protocol-level claims.

The observer and authority are under the same operator's control. The scenario
uses one fixed target and deterministic barriers; it measures neither general
race latency nor two-target coverage. Resuming a LangGraph interrupt could replay
the node and earlier side effects; resumption/durable recovery are outside the
frozen experiment. No interpretation in this table changes the saved native view.

## Exact field and guard trail

The following paths and line numbers refer to the bundled K3 commit
`76ecce0b378a6b391850795abf45fb6aca8e1d6b`, which contains D commit
`0130fcf8e7d70a0f9c4f977957e5de76ca8ef689` unchanged.

| Guard/source | Saved artifact or view field | Consequence |
|---|---|---|
| `integrations/langgraph/run.py:281-291` | `lifecycle.json[*].evidence[].ref/content_hash`; `event-mapping.json[*].source_event_ids` | Each emitted artifact points to the exact recorded event bytes; signatures authenticate the report, not independent event truth |
| `integrations/langgraph/run.py:322-328` | Execution `instruction_digest`, `executed_action_digest`, `execution_event=executed` | Receipt bytes and instruction must match; requested action/ID must match; native output and checkpoint interrupt IDs must match, and checkpoint next must be nonempty. Missing receipt/request/native pause cannot pass this guard |
| `integrations/langgraph/run.py:329-331` | Execution `execution_event=failed` and actual-action digest | A matching receipt with unavailable handler records failure; it does not become the successful branch |
| `integrations/langgraph/run.py:332-338` | Effect `execution_ref`, `observer_relationship=same_executor`, `observed_state.state_digest` | Both an emitted Execution and an actual effect observation are required; disabled observer emits no Effect |
| `tools/airep_v02/explain.py:74-93` | `explain.json.claim_matrix[*].source=/checks/N`, `source_check`, `source_status` | Native reconciler checks are copied without upgrading their states; lines 83-89 explicitly separate execution, enforcement, and causation |
| `tools/airep_v02/explain.py:95-104` | The row with `claim=enforcement_observed` has `source=null`, `source_check=null`, `source_status=null`, `explanatory_status=NOT_EVALUATED` | This unconditional unavailable-predicate branch states that the beta reconciler has no separate enforcement predicate. Even a guarded `execution_event=executed` cannot change it |
| `tools/airep_v02/explain.py:95-104` | The row with `claim=relying_party_claim_support` has the same null native fields and explanatory NOT_EVALUATED | The reconciler evaluates no relying-party claim or acceptance policy. The branch does not inspect local step counts to infer such support |

The K5 runner checks both unavailable-predicate rows in all six saved views and
reruns D's CLI on `stop-during-action/lifecycle.json` with that run's bindings and
revocation snapshot. Its output must equal the saved view. Null `source_status`
is absence of a native predicate, not a native success or failure state.
