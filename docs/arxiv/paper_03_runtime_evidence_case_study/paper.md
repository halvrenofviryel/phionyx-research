# Runtime Evidence for Agentic Development: Binding Self-Claims, Tool Calls, and Trace Events into Verifiable Governance Chains

*A case study in measuring and closing the stochastic input generation gap with deterministic runtime hooks*

**Author:** Ali Toygar Abak (Phionyx Research) — ORCID [0009-0002-3718-4010](https://orcid.org/0009-0002-3718-4010)
**Date:** 2026-05-27 (T+1 follow-up measurement integrated); title revision 2026-05-26; first draft 2026-05-26
**Pinned commit:** `0ffb9dd9` (Phionyx monorepo at T+1 measurement; previous pin `8595a7a6` at title-revision time)
**Categories:** primary `cs.SE` (software engineering); secondary `cs.AI`
**Keywords:** runtime governance, AI-assisted development, Model Context Protocol, audit chain, deterministic hooks, reproducibility, evidence-oriented telemetry, agentic AI.

---

## Abstract

When an AI assistant participates in writing the software that governs AI assistants, the assistant's own development becomes a load-bearing case for the governance claim. Phionyx publishes a runtime-evidence discipline: gates that produce signed, hash-chained records of every governed decision, paired with reviewer-runnable reproduction commands. We test that discipline against its own development workflow.

We define the **stochastic input generation gap**: gate logic is deterministic, but the inputs the gates receive are produced by a probabilistic model that controls its own compliance. We introduce a coverage metric computable from existing harness telemetry, $C(t) = |\mathrm{gate\_calls}(t)| / (2 \cdot |\mathrm{commits}(t)|)$, that distinguishes binding gate invocations from observability activity. A 30-day baseline measurement on the Phionyx monorepo at 2026-05-25 reads **7.5%**. We then introduce a binding enforcement layer — 12 Claude Code hooks split into 5 blocking and 7 observability — designed to close the gap without inflating the audit metric. We document a sequence of four interventions on 2026-05-26 (hook expansion, MCP-configuration canonicalisation, ADR-0006 trace unification, SessionStart trace reset) and report a same-day re-measurement of 9.5%. The +2 percentage points are heavily attributable to a single intervention-day session; the structural effect of the new hooks is a falsifiable forecast, not yet a measured outcome.

The contribution is not a single number but a discipline: a reproducible coverage measurement methodology, an honestly disclosed baseline, a binding mechanism that does not contaminate its own audit, and the explicit forecast that future audits will confirm or refute the mechanism's effectiveness. All numeric claims trace to a pinned audit-script invocation or to the canonical evidence table at the same commit. This paper is not a certification or detection benchmark; it is a reflexive instance of the protocol introduced in [@abak2026evidenceprotocol].

---

## §1 Introduction

The Phionyx Principles [@phionyx_manifesto_2026] commit to a specific reframe: *AI ethics statements are not enough. Governance must be executable at runtime.* The reframe is operational, not aspirational. Values that compile into signed, reviewer-runnable artefacts are practice; values that exist only in prose are not.

This commitment generates a dogfood obligation. If Phionyx publishes a runtime-evidence discipline for production AI systems, the AI-assisted development of Phionyx must demonstrate the same discipline at its own substrate level. The development substrate is **AI-pair-programming**: a human developer collaborating with a large-language-model coding assistant (Claude Code, in this case study) over a shared repository, where the assistant generates code, edits files, commits, pushes, and writes claims about what it did.

The case study question of this paper is direct: when the protocol introduced in [@abak2026evidenceprotocol] is applied to Phionyx's own development workflow, how much of the workflow is actually governed? We answer with a measured baseline, a documented intervention, and a falsifiable forecast.

### 1.1 The stochastic input generation gap

Phionyx's pipeline MCP exposes a set of gate tools (`phionyx_response_gate`, `phionyx_verify_claim`, and others, §4.1). The gates are deterministic: given the same input, they produce the same directive (`pass | reject | regenerate | rewrite`) according to published thresholds. The advisory rule in the project's `CLAUDE.md` is: *before claiming a fix is working, before deploying, before committing — call the gate*.

This rule trusts the assistant to call the gate. The assistant, however, has discretion over whether the call occurs at all, what inputs it provides, and what evidence type it declares. The gate is deterministic; the *upstream* of the gate is not. We name this the **stochastic input generation gap**: the unbridged distance between a deterministic control plane and a probabilistic invoker. The gap is not specific to LLMs — it is the same shape as "an advisory rule depends on the operator following it" in any system — but probabilistic operators make the gap structural rather than accidental.

A gap that cannot be measured cannot be closed. The first contribution of this paper is the measurement methodology (§5). The second is the measurement itself (§6). The third is the binding mechanism that closes the gap deterministically (§4.4). The fourth is the discipline of publishing all three together, at a pinned commit, so any reviewer can reproduce them.

### 1.2 Contributions

- **C1 (Methodology).** A reproducible measurement of *gate coverage* in AI-assisted software development, computed from harness telemetry that already exists in any deployment of the Phionyx pipeline MCP. The metric distinguishes binding gate invocations from observability activity by construction.
- **C2 (Honest baseline).** A 30-day measurement at 2026-05-25 reading **7.5%** coverage, with per-day disclosure showing the pattern is not flukish. The infrastructure was installed, configured, and active; it was simply not invoked on most commits.
- **C3 (Binding mechanism).** A layered enforcement design comprising 12 Claude Code hooks (5 blocking, including one always-on Stop hook; 7 observability). Blocking hooks refuse non-compliant actions; observability hooks log activity but are excluded from coverage math, preventing the audit from inflating itself.
- **C4 (Reviewer-runnable artefacts).** A single command (`python3 scripts/active/runtime_evidence_self_audit.py --days 30`) reproduces the measurement at any pinned commit against the same telemetry shape. The dashboard at `localhost:3005/runtime-evidence` renders the same numbers live.

### 1.3 Scope and identity boundary

This is a **case study**: n=1 codebase, n=1 developer, n=1 agent host (Claude Code), 30-day window. Generalisability is discussed in §9. The paper does not claim:

- *That hook-based enforcement makes LLMs deterministic.* It does not. It makes the control plane around the LLM deterministic.
- *That coverage is a sufficient condition for trustworthiness.* It is a necessary condition for the protocol to be honest about itself.
- *That AI accountability is a solved problem.* It is not. This paper specifies one falsifiable instance of one mechanism.

Per `.claude/rules/agi-architecture.md` Invariant 2, this work touches **mind-loop stage = none (infrastructure)**. Hook coverage is an automation-quality improvement, not a cognitive-progress claim.

### 1.4 Paper organisation

§2 introduces the substrate: the 46-block canonical pipeline, the Governed Response Envelope, Claude Code as agent harness, the two-layer MCP architecture. §3 formalises the stochastic input gap. §4 describes the system architecture: pipeline MCP, server MCP, shared trace contract, the 12 hooks. §5 specifies the measurement protocol. §6 reports the case study (baseline, intervention, post-measurement). §7 compares the protocol's coverage against four adjacent frameworks. §8 lists reviewer-runnable evidence. §9 documents limitations. §10 names future work. §11 concludes.

---

## §2 Background and substrate

### §2.1 The 46-block canonical pipeline

Phionyx Core ships a fixed-order pipeline of 46 blocks ([@phionyx_canonical_blocks_v3_8]), under contract version v3.8.0. The blocks span input safety, intent classification, retrieval, ethics gates, behavioural drift detection, physics-state computations ($\phi$, entropy, confidence fusion), response revision, and audit emission. Block order is canonical: blocks are never deleted, only policy-bypassed with an audit trail.

Of these 46 blocks, eleven are **governance-relevant** in the sense that they produce or consume runtime-evidence artefacts: `kill_switch_gate`, `input_safety_gate`, `knowledge_boundary_check`, `trust_evaluation`, `deliberative_ethics_gate`, `behavioral_drift_detection`, `phi_computation`, `entropy_computation`, `confidence_fusion`, `response_revision_gate`, `audit_layer`. The remaining 35 blocks are cognitive substrate (retrieval, perception, scenario framing, etc.) whose decisions are *observed* by the governance blocks but are not themselves audit producers.

The pipeline is the *target runtime* — the system that governs production AI applications using Phionyx Core. The present case study mirrors a subset of this discipline onto the *development runtime* — the AI-pair-programming session that builds the target runtime. The mirroring is not identical: the development runtime has no `phi_computation` block. But it has the same three structural primitives: deterministic gates, signed audit records, and reviewer-runnable reproduction.

### §2.2 The Governed Response Envelope (RGE v0.2)

The per-turn audit record specified in [@abak2026evidenceprotocol] is the **Governed Response Envelope (RGE)**. Its v0.2 schema, persisted by `phionyx-mcp-server` under `~/.phionyx/mcp_audit/<trace>/<turn>.json`, contains: `trace_id`, `turn_index`, `producer`, `user_text`, `tool_descriptor_hash` (used for tool-poisoning detection per Jamshidi et al. [@jamshidi2026mcp]), `descriptor_change_detected`, `tool_permission_scope`, `input_hash`, `output_hash`, `approval_state`, `anomaly_flag`, `decision`, `decision_reason`, `runtime_policy_basis`, and an `IntegrityBlock` (`previous`, `current`, `signature`, `public_key`).

The chain is tamper-evident: each envelope's `IntegrityBlock.current` is the SHA-256 of its canonical-JSON form; `IntegrityBlock.previous` references the prior envelope's `current`. Any modification at position $k$ breaks $k$'s `current` hash, which breaks $k+1$'s `previous` reference, which breaks the Ed25519 signature. `FilesystemEnvelopeStore.verify_chain` walks the chain and reports `{valid, broken_at, reason}`. See Figure 5 (Appendix C) for the field layout.

### §2.3 Claude Code as agent harness

The case study runs on Claude Code as the agent harness ([@anthropic_claude_code]). Claude Code exposes a hook lifecycle on which the binding layer described in §4.4 is wired: `SessionStart`, `UserPromptSubmit`, `PreToolUse` (with per-tool matchers including `Bash`, `Edit|Write|MultiEdit|NotebookEdit`, `Agent`, and `mcp__.*`), `PostToolUse` (with matchers including `Bash` and `WebFetch|WebSearch`), `Stop`, `SubagentStop`, `PreCompact`. Hooks are configured in `.claude/settings.json` (committed to the repository) and the harness executes them — the assistant cannot opt out.

This is structurally different from system-prompt instructions to the assistant. A system prompt is read by the assistant and complied with probabilistically. A hook is read by the *harness* and enforced deterministically. The distinction is the whole point of this paper.

### §2.4 Two-layer MCP architecture (ADR-0006)

Phionyx ships two MCP servers side-by-side in the same Claude Code session: `phionyx-pipeline` (self-governance of the assistant's own claims) and `phionyx-mcp-server` (MCP trust boundary for third-party tools per Jamshidi et al. [@jamshidi2026mcp]). [@adr0006_mcp_integration] documents the decision to keep them separate rather than merging them: different consumers, different release cadences (the server MCP is public AGPL-3.0 on PyPI; the pipeline MCP is internal repo tooling), different blast radius.

The two MCPs are nevertheless joined on a single `trace_id` per Claude Code session, so their telemetry can be correlated without merging the packages. Resolution order: `PHIONYX_TRACE_ID` env var; otherwise the contents of `~/.phionyx/active_trace`; otherwise a freshly generated UUID persisted to that file. The pipeline MCP's `phionyx_session_report` tool surfaces the server MCP's chain head via an optional `mcp_envelope_chain` field. See **Figure 1**.

![Figure 1 — Two-layer MCP architecture with shared trace_id](figures/fig1_two_layer_mcp.md)

> **Figure 1.** Both MCP servers resolve the active `trace_id` from the same coordination file. Pipeline MCP writes per-tool directive logs to project-local JSON; server MCP writes signed, hash-chained envelopes to home-directory JSON. `SessionStart` hook (§4.4) resets the coordination file on a new conversation. *(Source: `figures/fig1_two_layer_mcp.md`.)*

---

## §3 The stochastic input generation gap

### §3.1 Definition

Let $T$ be the set of tool calls an AI assistant performs in a session. Let $G \subseteq T$ be the subset that are governance-class gate calls (`phionyx_response_gate`, `phionyx_verify_claim`). Let $C \subseteq T$ be the subset that are commit-class actions (any tool call that ends in a `git commit` in the project's git log). The CLAUDE.md advisory rule requires at least two gate calls per commit (before claim-fixed and before commit). The **coverage metric** is:

$$
\mathrm{Coverage}(t) \;=\; \frac{|G(t)|}{2 \cdot |C(t)|}
$$

where $t$ denotes a measurement window (typically 30 days, matching the audit script's default).

### §3.2 Why advisory rules underperform

A coverage of 100% requires the assistant to invoke the gate at every commit boundary. Each invocation costs the assistant: extra latency, a context-window allocation for the gate's response, the cognitive load of constructing valid inputs (`action_type`, `confidence`, `evidence_count`, `evidence_type`). When the assistant balances "follow the rule and be slower" against "skip the rule and finish faster," and the rule is advisory, the second option is structurally available. Compliance is therefore probabilistic.

Two related properties:

1. **Input plausibility is also stochastic.** Even when the assistant *does* invoke the gate, it constructs the inputs from its own perception of the situation. The gate decision is only as good as the assistant's framing of the evidence. We do not address this second-order problem in this paper; we treat it as a deployer responsibility (see §9) and focus on the first-order problem of whether the gate is invoked at all.

2. **Observability is not coverage.** A naive metric that counts all MCP activity would rise mechanically as the harness emits more telemetry. The discipline of this paper requires the coverage metric to measure *binding gate invocations* — calls that block bad outcomes — not activity volume.

### §3.3 The distinction from per-turn validation

Per-turn validation, output guardrails, and per-task benchmarks cannot, by construction, measure coverage of this kind. They observe what the assistant *says*, not whether it *invoked a gate before saying it*. The stochastic input gap is a property of the *trajectory* — manifesto §1's framing. Closing it requires harness-level instrumentation, which is what hooks provide.

---

## §4 System architecture

The runtime-evidence stack instantiated on the Phionyx repository has four layers: a pipeline MCP for self-governance, a server MCP for third-party trust boundary, a shared-trace coordination contract, and twelve harness hooks that bind invocation.

### §4.1 Pipeline MCP (`tools/claude_code_mcp/phionyx_claude_mcp.py`)

Six tools, mounted on Claude Code via the project's `.mcp.json`:

| Tool | Responsibility | Telemetry write? |
|---|---|---|
| `phionyx_verify_claim` | Three-layer claim verification: LLM declaration → `git diff` truth → physics gate decision | yes |
| `phionyx_response_gate` | Deterministic revision gate with action-type-specific thresholds (`claim_fixed`, `deploy`, `default`, `refactor`, `investigate`, `ask_question`) | yes |
| `phionyx_verify_paths` | Cross-check declared `affected` and `tested` paths against actual `git diff` | no |
| `phionyx_causal_trace` | Validate causal chains for debugging: ≥3 links, ≥40% code-path specificity | no |
| `phionyx_checkpoint` | Lightweight physics snapshot (no diff, no verification) — used to keep the telemetry timeline dense for live monitoring | yes |
| `phionyx_session_report` | Aggregate the session: claims, directives, drift metrics, evidence taxonomy, current physics state, `mcp_envelope_chain` join with server MCP | no |

Of these six, three (`verify_claim`, `response_gate`, `checkpoint`) write to the session telemetry file (`data/mcp_telemetry/session_<trace>.json`) and contribute to the audit's `all_calls` count. Two of those three (`verify_claim`, `response_gate`) carry `gate-class` directives and count toward `gate_calls`. The remaining four tools are read-only inspectors that do not pollute the coverage metric.

### §4.2 Server MCP (`tools/phionyx_mcp_server/`)

Eight declared capabilities, two implemented at the time of this commit, six declared as stubs to be wired against future telemetry sources:

- **Implemented.** `verify_tool_descriptor` (hashes the descriptor and detects post-approval drift — the rug-pull defence per [@jamshidi2026mcp]); `record_tool_call` (builds and persists a v0.2 RGE envelope with `mcp_tool_audit` block).
- **Stubs.** `verify_chain_integrity`, `query_audit_history` (walked-chain queries — stubbed because the chain is currently empty for most traces; the implementation exists in `audit_chain.py` but the MCP wrapper is deferred until the chain reaches non-trivial depth); `flag_anomaly`, `audit_record_decision`, `record_user_approval` (reserved).

The envelope chain is replayable from the persisted JSON alone. A reviewer with the producer's Ed25519 public key can verify any chain without access to the operator's infrastructure — the manifesto §5.1 commitment expressed at the schema level.

### §4.3 Shared trace contract (ADR-0006)

Trace resolution per [@adr0006_mcp_integration] §"Shared identifier — `PHIONYX_TRACE_ID`":

1. If `PHIONYX_TRACE_ID` env var is set, use it.
2. Otherwise read `~/.phionyx/active_trace` (single-line text file).
3. Otherwise generate a fresh UUID and persist it to that file.

The `PHIONYX_ACTIVE_TRACE_FILE` env var overrides path (2) but is intentionally unset in production configuration: both MCPs are expected to default to the same home-directory path, which is the minimum coordination that does not require either MCP to know the other exists. A divergent project-relative override on the server MCP — present in earlier versions of the configuration — was found to silently break the contract at runtime; commit `0d66e17d` removed it.

`SessionStart` hook resets the coordination file on `source == "startup"`, so each new Claude Code conversation receives a fresh trace. `resume`, `clear`, and `compact` preserve the trace because they continue the same logical session. This closes the ADR-0006 open follow-up.

### §4.4 The 15 hooks

Hooks are configured in `.claude/settings.json` (committed). The harness invokes them; the assistant cannot opt out. **Figure 2** shows the wiring.

The hook layer landed in two waves. The v0.6.x baseline of 12 hooks (rows 1–12 below) closed the binding-input gap for actions Claude *takes*. The v0.7.2 expansion (rows 13–15) closes the *feedback* gap for actions Claude *produces*: per-edit language-tool feedback, per-Stop targeted test execution, and the schema validator for the assistant's own memory layer (F-MS1, shipped in v0.7.1 and listed here for completeness).

![Figure 2 — Claude Code lifecycle with 15 hook attachment points](figures/fig2_hook_lifecycle.md)

> **Figure 2.** Five hooks **block** non-compliant actions (red); ten observe and attest (blue). Blocking hooks form the binding layer that closes the stochastic input gap. Observability hooks add density to the telemetry timeline but are excluded from coverage math by construction (§5.3). The three v0.7.2 additions (rows 13–15) feed per-edit and per-Stop signals back to the assistant so corrections happen in the same turn. *(Source: `figures/fig2_hook_lifecycle.md`.)*

**Table 1.** *Hook inventory. Strict mode (`PHIONYX_MCP_GATE_STRICT=1`) is the production setting. Rows 13–15 added in v0.7.2 (2026-05-27); row 7 (memory schema) added in v0.7.1.*

| # | Script | Event + matcher | Class | Strict-mode action | Soft-mode action |
|---|---|---|---|---|---|
| 1 | `check_mcp_gate.py` | `PreToolUse` / `Bash` (git commit \| push) | **blocking** | BLOCK if no gate call ≤ 5 min | WARN |
| 2 | `check_bash_external_effect.py` | `PreToolUse` / `Bash` (gh, npm, twine, docker, kubectl, terraform, destructive git) | **blocking** | BLOCK if no gate call ≤ 5 min | WARN |
| 3 | `check_edit_gate.py` | `PreToolUse` / `Edit \| Write \| MultiEdit \| NotebookEdit` | **blocking** (edits > 20 lines) | BLOCK if no gate call ≤ 30 min | WARN |
| 4 | `check_agent_spawn.py` | `PreToolUse` / `Agent` | **blocking** | BLOCK if no gate call ≤ 30 min | WARN |
| 5 | `check_question_grounding.py` | `Stop` | **blocking** (always-on) | BLOCK if response asks about unread artefact | BLOCK (no soft mode) |
| 6 | `check_mcp_tool_call.py` | `PreToolUse` / `mcp__.*` | observability | log `mcp_tool_invocation` | log |
| 7 | `session_start_attest.py` + `check_memory_schema.py` (F-MS1, v0.7.1) | `SessionStart` | observability | log `session_start`, reset trace on `startup`; validate memory frontmatter against `MemoryFrontmatter` Pydantic model (`PHIONYX_MEMORY_STRICT=1` blocks) | log |
| 8 | `log_user_prompt.py` | `UserPromptSubmit` | observability | log SHA-256 + length | log |
| 9 | `pre_compact_checkpoint.py` | `PreCompact` | observability | log `pre_compact_checkpoint` | log |
| 10 | `attest_subagent_stop.py` | `SubagentStop` | observability | log `subagent_complete` | log |
| 11 | `auto_attest_commit.py` | `PostToolUse` / `Bash` (git commit) | observability | log `commit_attestation` (SHA) | log |
| 12 | `log_external_ingress.py` | `PostToolUse` / `WebFetch \| WebSearch` | observability | log `external_ingress` (URL + size) | log |
| 13 | `post_edit_language_check.py` (**v0.7.2 P2**) | `PostToolUse` / `Edit \| Write \| MultiEdit \| NotebookEdit` | observability | dispatches by extension: `.py` → `py_compile` + `ruff`; `.ts/.tsx` → scoped `tsc --noEmit`; `.json` → `json.tool`; `.yaml/.yml` → `yaml.safe_load`; memory `.md` → `check_memory_schema.py`. ≤ 8 s/file, ≤ 25 output lines. Writes findings to stderr | log |
| 14 | `run_targeted_tests.py` (**v0.7.2 P4**) | `Stop` | observability | walks `git diff` + `git diff --cached` + last commit, routes changed paths to test directories (11-route table); runs `pytest -q` with per-target timeout (60s/4 = 15s/target). Honors `stop_hook_active=true` per Anthropic guidance to avoid Stop-loop. Writes pass/fail summary to stderr | log |
| 15 | `check_memory_schema.py` (also at SessionStart, row 7) — listed separately when invoked by `post_edit_language_check.py` for `.md` files under the auto-memory directory | invoked from row 13 | observability | F-MS1 schema validation | log |

**Critical design rule.** All observability hooks emit `directive: "auto_attest"` entries to the session telemetry. The self-audit script (§5) explicitly excludes `auto_attest` directives from the `gate_calls` count. Inflating the coverage metric by counting observability activity would defeat the audit; the design rule prevents this by construction.

**Figure 3** traces one commit cycle through the stack.

![Figure 3 — Data flow from prompt to coverage metric](figures/fig3_data_flow.md)

> **Figure 3.** Each commit traverses two blocking gates (pre-Edit and pre-commit-Bash). Successful commits emit a `commit_attestation`. The Stop boundary now runs targeted tests (row 14) so post-claim verification is automatic. The self-audit script later reads the resulting telemetry plus `git log` and produces a deterministic coverage report. *(Source: `figures/fig3_data_flow.md`.)*

### §4.5 Subagent layer — fresh-context adversarial review (v0.7.2 P1)

The hook layer (§4.4) covers what Claude is about to *do*. It does not catch semantic bugs in the *content* the assistant produces: a typed interface that drifts from its data shape, a CLI that signals data status through its process exit code, a UI label that hardcodes a version after subsequent releases shipped. These were the four bugs that landed in production on 2026-05-27 despite the 12-hook layer being active. Three of the four are caught by no hook because the diff was syntactically valid, type-checked locally, and passed the gates: the bugs were *semantic*, visible only on top-of-stack review.

We add an **adversarial diff-reviewer subagent** as a separate layer above the hooks. It is defined at `.claude/agents/diff-reviewer.md` and invoked with the natural-language prompt *"Use the diff-reviewer subagent to check this commit."* The agent runs in a fresh context window — it has not seen the reasoning that produced the diff, only the diff itself plus the stated acceptance criteria — with a Read-only tool set (`Read`, `Grep`, `Glob`, `Bash`). It cannot edit, commit, or invoke external-effect commands.

The agent's prompt enumerates seven correctness-affecting finding categories: (A) schema / interface / contract drift; (B) exit-code / signal anti-patterns; (C) bucketing / aggregation bugs; (D) version / URL / repo drift; (E) test coverage drift; (F) hidden state-fact assertions in public copy; (G) AGI / governance invariant labelling. Style preferences, defensive-programming flags, and refactoring suggestions outside the diff's scope are explicitly skipped. The agent is calibrated against the four 2026-05-27 bugs: the prompt's calibration footer notes the specific finding category for each so future revisions can verify the prompt would still catch them.

The subagent is **complementary, not redundant**, to the hook layer:

- Hook 13 (`post_edit_language_check.py`) catches **syntactic** drift (the consuming TypeScript file fails to type-check after a producer adds a new field). It runs after every Edit; cheap, bounded, immediate.
- The diff-reviewer subagent catches **semantic** drift (the consumer is type-correct against the old schema, but the schema and data shape have drifted). It runs in a fresh context only when explicitly invoked; expensive, slow, higher signal-per-token.

Cost rationale: invoking the diff-reviewer subagent on every commit would burn cache and tokens unnecessarily for low-risk changes (typo fixes, documentation edits). The protocol is to invoke it for commits that touch the seven sensitive categories (multi-file refactors, schema changes, public-copy edits, version bumps, governance-module edits). For longer autonomous runs, an `agent-team`-style configuration could pin the reviewer as a continuous shadow process; this is a v0.8.0 candidate.

**Why subagents and not another hook.** Hooks have a deterministic trigger (lifecycle event + matcher) and bounded runtime. A semantic reviewer needs to *read the diff* and *form a judgement*, which is itself an LLM call. Encoding it as a hook would either require a model invocation inside the hook script (slow, expensive, blocks the workflow) or limit it to syntactic checks (the language-tool hook's scope). The Anthropic subagent abstraction is the right granularity: it isolates the review in its own context, gives it tools but not write access, and returns findings as a tool result that the implementing session can act on.

---

## §5 Measurement protocol

### §5.1 The self-audit script

The script at `scripts/active/runtime_evidence_self_audit.py` is the canonical measurement tool. Its inputs are `data/mcp_telemetry/session_*.json` (the telemetry written by the pipeline MCP and the observability hooks) and `git log` for the same window. Its output is a markdown report at `docs/strategic/runtime_evidence_self_audit_<DATE>.md`. The script is deterministic: given the same inputs, it produces the same output.

The script's CLI signature is intentionally minimal:

```bash
python3 scripts/active/runtime_evidence_self_audit.py --days 30
```

No other flags are required. The default 30-day window matches the cadence at which the founder reviews the metric.

### §5.2 Coverage definition

The script computes:

$$
\mathrm{Coverage}(t) \;=\; \frac{|G(t)|}{2 \cdot |C(t)|}
$$

where $G(t)$ counts `gate-class` directives (`phionyx_response_gate`, `phionyx_verify_claim`) within the window $t$, and $C(t)$ counts commits in the project's git log within the same window. The 2× multiplier encodes the CLAUDE.md rule: one `verify_claim` before claiming a fix, one `response_gate` before committing. The denominator is therefore conservative: the assistant may legitimately do significant work outside commit boundaries (research, dry runs, planning) without being penalised, but it is required to gate every commit twice.

### §5.3 Why `auto_attest` exclusion is load-bearing

The seven observability hooks emit `auto_attest` directives. If the script counted them as `gate_calls`, the metric would rise mechanically with every hook expansion, without any improvement in the discipline the metric is meant to measure. The script's behaviour is documented at `tools/claude_code_mcp/_telemetry.py:10–14`:

> *"Attestation entries written here use `directive='auto_attest'` and are NOT counted toward the `/runtime-evidence` dashboard's `gate_calls` metric — inflating that would defeat the audit. They contribute to `all_calls` so density/coverage signals are still visible."*

This is the design rule that makes the metric honest. Without it, the audit would be self-marketing.

### §5.4 Public reproduction

Any reviewer with a clone of the public repository can run the script:

```bash
git clone https://github.com/halvrenofviryel/phionyx-research
cd phionyx-research
git checkout 4bca5f3e            # pinned commit for this paper
python3 scripts/active/runtime_evidence_self_audit.py --days 30
```

The output matches the report cited in §6, within the limit that the reviewer's clone may have a different telemetry archive (the telemetry is the dataset; the script is the deterministic transformation).

---

## §6 Case study: closing the gap

### §6.1 Baseline measurement (2026-05-25)

The baseline audit at 2026-05-25 covers the 30-day window ending that date. The audit script reports:

- **261** commits in the window
- **39** gate calls
- Expected gate calls per CLAUDE.md: **522** (= 261 × 2)
- **Coverage: 7.5%**

Per-day breakdown (excerpted from the audit report at `docs/strategic/runtime_evidence_self_audit_2026-05-25.md`): of 26 days in the window, 22 had zero gate calls; the remaining four had partial activity (2026-04-28 with 33 gate calls but 0 commits — an integration-test session, see §9; 2026-05-24 with 4 gate calls and 26 commits; 2026-05-25 with 2 gate calls and 28 commits).

### §6.2 Honest reading of the baseline

The infrastructure existed. The pipeline MCP was installed, configured, and active. The CLAUDE.md rule was published and visible. The assistant did not invoke the gates on most commits. **This is the stochastic input gap, measured.**

More concretely: in every Claude Code session of this 30-day window, the pipeline MCP was loaded, its gate tools were callable, and the CLAUDE.md rule was visible in the assistant's system reminder on every turn. None of those three conditions produced binding compliance. The 7.5% is therefore not a measurement of missing infrastructure or of the rule's invisibility — it is a measurement of *what an advisory rule alone produces when its operator is probabilistic*. The remaining 92.5% is the gap that the binding layer (§4.4) is designed to close.

The reading is not an indictment of any single session. It is a structural observation: an advisory rule whose compliance depends on the agent's discretion will, over a sufficiently long window, exhibit non-trivial non-compliance. The 7.5% is the *magnitude* of the gap; the 92.5% is the *evidence* that the gap is real.

### §6.3 Intervention sequence (2026-05-26)

The interventions were not the hypothesis-then-test of a controlled study; they were a sequence of repository changes intended to close the gap, made over the working day of 2026-05-26 and committed as the work progressed. Four are load-bearing:

1. **Hook expansion (commit `af45aec1`).** Six new observability hooks and two new blocking hooks (PreToolUse on `Agent`, PreToolUse on Bash external-effect patterns) added to `.claude/settings.json`. NotebookEdit added to the existing edit-gate matcher. Total hook count after this commit: 12 (5 blocking + 7 observability).

2. **MCP configuration canonicalisation (commit `0d66e17d`).** Two `mcp.json` files had been coexisting in the repository (`.claude/mcp.json`, which was tracked, and `.mcp.json`, which was gitignored). Claude Code actually loaded the gitignored one. Previous "canonical" fixes had been touching the tracked-but-unused file. We removed the unused `.claude/mcp.json`, removed `.mcp.json` from `.gitignore`, and tracked it as canonical.

3. **ADR-0006 trace unification (commit `0d66e17d`, same commit).** The server MCP had been configured with `PHIONYX_ACTIVE_TRACE_FILE=.phionyx/active_trace` — a project-relative override that diverged from the pipeline MCP's home-directory default. Both MCPs were reading from different files and resolving different trace IDs in the same session. We removed the override; both now default to `~/.phionyx/active_trace`, restoring the ADR-0006 contract.

4. **SessionStart trace reset (commit `4bca5f3e`).** The ADR-0006 open follow-up: on `source=startup`, the SessionStart hook now unlinks `~/.phionyx/active_trace` so a fresh trace is generated. Other sources (`resume`, `compact`, `clear`) preserve the trace.

All four interventions are committed and pushed to `origin/main`. The pre-commit governance hook (Core boundary check, Secret scan, Lint check, MCP gate check) passed for each. Post-restart verification confirmed pipeline MCP and server MCP report the same `trace_id` in their respective output.

### §6.4 Post-intervention measurement (2026-05-26)

The same audit script, re-run after the interventions, reports:

- **269** commits in the window
- **51** gate calls
- Expected gate calls per CLAUDE.md: **538** (= 269 × 2)
- **Coverage: 9.5%**

Per-day breakdown: the window now includes 2026-05-26, which by itself reads **85.7%** coverage (7 commits, 12 gate calls). The high single-day coverage is the author's working session that produced the interventions; it is heavily gated because the work touched MCP infrastructure and edit-gate / commit-gate hooks fired aggressively.

### §6.4.1 T+1 follow-up measurement (2026-05-27) — and a measurement-bug retraction

A first version of this section, written at 2026-05-27 17:19 UTC using the audit script alone, reported 2026-05-26 at **81.2%** single-day coverage (40 commits, 65 gate calls) and 2026-05-27 at **0%** (13 commits, 0 gate calls). Both readings were wrong. The error illustrates a hazard the rest of this paper argues for guarding against: an instrument that under- or over-reports its own measurements.

Root cause: `scripts/active/runtime_evidence_self_audit.py` bucketed every timeline entry of a session into the date the *session* began, not the date the *entry* itself happened. The live working session that produced the interventions of §6.3 started 2026-05-26 13:48 UTC and was still active 24+ hours later. Every gate call made on 2026-05-27 in that long-lived session was therefore attributed to 2026-05-26. The Founder Console API at `apps/founder-console/app/api/runtime-evidence/route.ts` bucketed correctly (by `entry.timestamp`), surfacing the discrepancy: FC showed 2026-05-26=38 / 2026-05-27=29, summing to 67 — the same total the buggy script lumped onto 2026-05-26 alone. The bug was fixed at commit `ecbd042f` and the audit re-run; the post-fix readings are below.

The audit script, **post-fix**, re-run at 2026-05-27 (later in the working day, post-bug-fix), reports:

- **317** commits in the window
- **106** gate calls
- Expected gate calls per CLAUDE.md: **634** (= 317 × 2)
- **Coverage: 16.7%**

Per-day breakdown (showing the two days most relevant to the forecast):

- **2026-05-26** — **46.2%** (40 commits, 37 gate calls). The single-day intervention figure. The earlier 85.7% reading in §6.4 was a 17:19-snapshot during the same intervention session; the early-day reading was based on 7 commits / 12 calls because the day's commit volume was still building. The full-day post-fix figure (46.2%) is the honest one. The earlier 81.2% claim was the bug.
- **2026-05-27** — **93.8%** (16 commits, 30 gate calls). The first full day of activity *after* the intervention. Higher than the intervention day itself, because the binding-active hooks fired on the working session that drafted this paper.

Two reading-level observations follow. First, the *shape* the structural forecast (§6.5) predicts — a baseline window dominated by 0% days, punctuated by post-intervention days at >40% (heavily gated days at >90%), with the rolling 30-day metric responding monotonically to days that fall in or out of the window — is the shape these two days actually exhibit. Second, the rolling 30-day figure moved from 9.5% on 2026-05-26 to **16.7%** on 2026-05-27 — a +7.2 percentage-point shift driven by both intervention-day and post-intervention-day calls remaining in the rolling window while pre-intervention days rolled off.

The retraction is consequential for the paper's discipline, not for its conclusions. The post-fix figures still satisfy the forecast's "shape" criterion. They do *not* yet substantiate it as a structural claim (one or two heavily gated days in a 30-day rolling window cannot). The 30-day-out audit (target: 2026-06-26) remains the falsifiable test. The honest reading: T+1 is consistent with the forecast, not evidence of it.

This sub-section explicitly preserves the wrong numbers above the fold so that any reader who saw the first version of this paper can verify the correction. The lesson — *the measurement layer itself is part of the trust chain, and bugs in the measurement layer can produce confidently wrong claims* — is the same lesson the rest of the paper applies to assistant-generated code. Cross-reference: `feedback_verify_state_before_asserting.md` in the project's Claude-Code memory directory codifies this exact discipline.

### §6.5 What the baseline–post pair proves and does not prove

Restricted to the single post-intervention day, coverage reads **85.7%** (7 commits, 12 gate calls). This is not yet a structural claim about the new layer. It is the first day of activity under it, and the author's session was unusually gate-heavy because the work itself touched gate infrastructure. But it is the **first existence proof** that compliance jumped under the same agent (Claude) on the same codebase, with only the binding mechanism having changed. The baseline window contained no session that produced this rate; the post-intervention window contains one.

The +2 percentage points in the rolling 30-day metric are heavily attributable to that single intervention-day session. **They are not yet the structural effect of the binding hooks.** The new hooks only fire on activity that occurs *after* their commit (`af45aec1`), and the 30-day window mostly precedes that commit.

What the pair *does* prove:

- The measurement methodology is reproducible: the script ran twice, against the same telemetry shape, and produced two reports with consistent structure.
- The infrastructure responds to the interventions in the expected direction: a gate-heavy day produced a measurable lift.
- The audit metric is non-trivial to satisfy: even a heavily gated day (85.7%) does not move the 30-day rolling average to a "satisfactory" reading.

What the pair does *not* prove:

- That the hook layer closes the structural gap. The hooks were committed today; their effect on future activity is a forecast, not a measurement.
- That the next 30 days will show substantially higher coverage. We forecast they will, but the falsifiable framing is: re-running the audit in 30 days should show structurally higher coverage. **If it does not, the hook design is wrong, and this paper's mechanism claim fails.**

### §6.6 Mechanism verification — scenario tests

The audit script (§5) measures *aggregate* coverage from telemetry. It tells the reviewer *that* the binding layer was invoked X% of the time, not *whether* each invocation behaves as designed. A reviewer who reads §5.3's claim — "observability hooks are excluded from coverage math" — has no direct evidence that this exclusion was actually programmed. The same reader, reading §4.4's claim that "blocking hooks refuse non-compliant actions", has no direct evidence that the refusal logic is correct under adversarial inputs.

To bridge that gap, we ship a deterministic scenario suite at `scripts/active/runtime_evidence_test_scenarios.py`. The suite exercises 13 individual mechanisms with synthetic inputs and records pass/fail per scenario in a reviewer-runnable report under `docs/strategic/test_scenarios_<DATE>.md`. The suite runs without restart, without modifying any session state, and without dependency on the harness — it spawns the hook scripts with synthetic JSON payloads on stdin and inspects their stdout/stderr exactly as Claude Code would.

**Table 3.** *Scenario coverage. Group A targets pipeline-MCP self-governance; group B targets the server-MCP trust boundary; group C exercises the harness-hook binding layer with synthetic stdin; group D verifies cross-layer integration.*

| #  | Group        | Mechanism under test |
|----|--------------|----------------------|
| A1 | Pipeline MCP | `phionyx_response_gate` produces non-pass directive under low confidence + no evidence (claim_fixed action). |
| A2 | Pipeline MCP | `phionyx_session_report` returns the active `trace_id` and the joined `mcp_envelope_chain` field. |
| B1 | Server MCP   | `verify_tool_descriptor` detects post-approval descriptor drift (the rug-pull defence). |
| B2 | Server MCP   | `verify_tool_descriptor` does *not* fire a false positive on an unchanged descriptor. |
| C1 | Hook layer   | `check_mcp_gate.py` (hook-mode) passes through non-commit `Bash` commands without gating them. |
| C2 | Hook layer   | `check_mcp_gate.py` ignores non-`Bash` tool invocations. |
| C3 | Hook layer   | `check_mcp_gate.py` matches the extended regex on `merge`, `rebase`, `cherry-pick`, `make-commit` (M1, commit `0963610a`). |
| C4 | Hook layer   | `check_edit_gate.py` emits `{"decision":"block",...}` on a > 20-line Edit when the session telemetry holds no recent gate call (strict mode). |
| C5 | Hook layer   | `session_start_attest.py` unlinks `~/.phionyx/active_trace` on `source=startup`. |
| C6 | Hook layer   | `session_start_attest.py` preserves the trace on `resume`, `clear`, `compact`. |
| C7 | Hook layer   | `auto_attest_commit.py` writes a `commit_attestation` entry to telemetry on a successful commit. |
| C8 | Hook layer   | `check_question_grounding.py` emits `{"decision":"block",...}` when a synthetic transcript shows the draft assistant message asking a question about an unread `.md` artifact. |
| D1 | Cross-layer  | Pipeline MCP and server MCP independently resolve to the same active `trace_id` (ADR-0006). |

**Pre-restart result, 2026-05-26 (pinned commit `dcc0c52f`):** **13 / 13 passed**. Per-scenario evidence: `docs/strategic/test_scenarios_2026-05-26.md`. Two scenarios (C4, C8) were initially flagged as "informational pass" — they returned a non-block response under the synthetic payload, leaving open whether the *block* path was wired or only the *pass* path was wired.

**Post-restart result, 2026-05-26 (pinned commit `c03f4ebd`):** **13 / 13 passed**, with C4 strengthening from "informational pass" to a hard block-JSON emission as a side-effect of the fresh session telemetry. Per-scenario evidence: `docs/strategic/test_scenarios_2026-05-26_postrestart.md`. C8 still required deeper fixture instrumentation, which is supplied in the next pass.

**Hardened-fixtures result, 2026-05-26 (this commit):** **13 / 13 hard-pass** — every scenario in group C that previously relied on ambient session state now exercises its block path against a hermetic synthetic fixture. Two changes carry this:

- **C4 fixture.** A temporary directory is set as `PHIONYX_TELEMETRY_DIR` (a new env override added to `check_edit_gate.py` and `_telemetry.py` so the script's `TELEMETRY_DIR` constant can be redirected for tests). A session JSON with empty-of-gate-calls timeline is written into the tempdir, and a synthetic 40-line `Edit` payload is sent. The hook emits `{"decision":"block","reason":"BLOCKED by check_edit_gate (no gate calls yet this session)..."}` deterministically.
- **C8 fixture.** A synthetic transcript JSONL is built with a user message followed by an assistant draft that asks a question (`Should I update the contents of foo.md?`) about an artifact the turn never `Read`. With `stop_hook_active=False`, the hook emits `{"decision":"block","reason":"BLOCKED by Phionyx Stop hook (check_question_grounding): Draft response asks a question that references artifact(s) not opened this turn: foo.md ..."}`.

The post-restart run additionally verified two independent facts the fixtures alone cannot:

- **C7** wrote its `commit_attestation` to a freshly-created session file (counter `0 → 1`), confirming that the binding chain re-initialises cleanly on MCP restart rather than carrying state implicitly across sessions.
- **A2 + D1** both still resolve to `trace-e2dd588aaf4d4c97` after restart: the shared-trace coordination via `~/.phionyx/active_trace` survives MCP reconnect, as ADR-0006 §"Shared identifier" requires.

**A scope caveat on what "restart" means.** `/mcp restart` reconnects the two MCP servers but does *not* trigger Claude Code's `SessionStart` event — that event fires only on a *full* Claude Code conversation restart. Consequently, **C5** (SessionStart unlinks `~/.phionyx/active_trace` on `source=startup`) is verified by the scenario suite via a synthetic stdin payload to `session_start_attest.py`, but is not exercised by `/mcp restart`. A full Claude Code restart in a future session would additionally re-verify C5 against the harness rather than against the synthetic payload; the verification under the synthetic payload is sufficient to demonstrate the script's behaviour, but the end-to-end harness invocation is currently out of scope for the suite.

**Independent live evidence (out-of-band).** During this session's authoring, an attempted `git push` from the assistant was blocked by the new `check_mcp_gate.py --hook-mode` (commit `dcc0c52f`) with the message `MCP_GATE: BLOCKED — last verify_claim/response_gate was 5.7 min ago (threshold 5.0 min, session ...)`. This is not part of the scenario suite (the suite uses synthetic payloads) but is a live confirmation that the new hook-mode emits valid `{"decision":"block","reason":"..."}` JSON to Claude Code's harness and that the harness honours it. The push only succeeded after a fresh `phionyx_response_gate` call brought the recency back inside the 5-minute window.

**Why this complements the audit.** The audit measures the proportion of commits that traversed the binding layer; the scenario suite verifies that the binding layer behaves correctly *when* it is traversed. The two together close the falsifiability loop: a reviewer can check (a) how often the gate fired (audit) and (b) whether the gate fired correctly (scenarios) on a single repository at a single pinned commit, with no operator infrastructure required.

**Scope reminder.** The binding layer measured here is the *self-governance MCP* layer (Appendix D, layer 3). Six other layers compose the full Phionyx runtime evidence programme — see Appendix D for the inventory and the cross-paper reading map. Coverage measurements in this paper do not represent any of the other six layers; their evaluation is future work.

**Figure 4** plots the timeline.

![Figure 4 — Coverage timeline](figures/fig4_coverage_timeline.md)

> **Figure 4.** Daily coverage on the Phionyx repository, 2026-04-26 → 2026-05-26. The 30-day rolling baseline at 2026-05-25 reads 7.5%; the re-measurement at 2026-05-26 reads 9.5%. The single 85.7% day is the intervention session itself. The structural effect of the new hooks is a falsifiable forecast for the next 30-day window. *(Source: `figures/fig4_coverage_timeline.md`. PDF render via `render_figures.py`.)*

### §6.7 Threat model — what the binding layer is and is not designed to stop

The hook layer (§4.4) is designed against a specific threat: a probabilistic operator that has incentive (latency, context budget, perceived speed) to skip the advisory gate the project's `CLAUDE.md` requires. The threat is *not* a malicious operator deliberately seeking to defeat the audit, nor an attacker with shell access to the developer machine. Mapped against the Jamshidi et al. MCP threat taxonomy [@jamshidi2026mcp] and a STRIDE-style decomposition:

| Threat class | In scope for the hook layer | Out of scope (mitigation depends on a different layer) |
|---|:---:|:---|
| **Spoofing** — agent claims to have called the gate when it did not | ✓ in scope | — |
| **Tampering** — agent or operator modifies past envelopes after the fact | partial | Tamper detection: yes (Ed25519 + hash chain, §2.2). Tamper *prevention* against a local-shell attacker: requires WORM storage adapter (M3 in the supplement). |
| **Repudiation** — agent denies having made a claim | ✓ in scope | — |
| **Information disclosure** — secrets leak through evidence chain | n/a for hooks | Operator responsibility: input/output hashes are recorded; raw payloads optional. |
| **Denial of service** — operator disables hooks | out of scope | Detection: yes (`runtime_evidence_self_audit.py` will show coverage drop). Prevention: requires `PHIONYX_MCP_GATE_STRICT=1` + CI enforcement (deployer responsibility, per the protocol's row schema). |
| **Elevation of privilege** — agent invokes a tool it should not | out of scope | Authorisation: handled by Claude Code's permission model + MCP server's `tool_permission_scope` field. The hook records; it does not authorise. |
| **Tool poisoning** (MCP threat taxonomy) | partial | Detection via `verify_tool_descriptor` (server MCP, App. D's MCP-outward layer). The pipeline MCP hooks instrument self-claim, not third-party tool descriptor verification. |
| **Shadowing** (MCP threat taxonomy) | out of scope | Server MCP's responsibility; cross-tool context contamination needs runtime descriptor monitoring. |
| **Rug pulls** (MCP threat taxonomy) | partial | `verify_tool_descriptor` detects descriptor drift between approval and use; documented in the server MCP layer (App. D), not in the hooks measured here. |

The honest reading: the hook layer described in this paper closes the *advisory-rule compliance* gap (Spoofing + Repudiation) for a non-adversarial operator. It detects but does not prevent advanced attacks; prevention requires the additional posture items the supplement names as M3.

### §6.8 Ablation — which hook contributes which coverage component

A formal ablation experiment (disable hook X, replay the same 30-day workload, measure coverage delta) requires (a) a stable measurement window and (b) a corpus of past sessions that can be replayed under different hook configurations. Neither is available within this paper's window. We document the **expected** per-hook contribution by reading the hook scripts and their attach points; a future audit (L2 in the supplement) will replace these expectations with measured deltas.

**Table 3.** *Per-hook expected contribution. Coverage measured by the audit script (§5.2) counts only blocking-class gate calls (`auto_attest` excluded).*

| Hook | Class | Removal expected impact on coverage metric | Expected impact on binding behaviour |
|---|---|---|---|
| `check_mcp_gate.py` | blocking | Major — commit-class events stop triggering gate enforcement | Commits proceed without gate; coverage falls to whatever rate the operator chooses voluntarily |
| `check_bash_external_effect.py` | blocking | Minor on the metric (external-effect events are not commits) | Deploys / publishes proceed without gate; tamper-evidence on those events lost |
| `check_edit_gate.py` | blocking | Moderate — every large edit currently requires a recent gate; removal reverses that pressure | Edits proceed without gate; advisory-only compliance returns |
| `check_agent_spawn.py` | blocking | Minor — subagent spawns are infrequent | Subagent claims become opaque to the parent session's audit |
| `check_question_grounding.py` | blocking (always-on) | No metric impact (questions are not commits) | Read-before-asking discipline lost; question-answering hallucination risk rises |
| `session_start_attest.py` | observability | No metric impact (excluded from `gate_calls`) | Trace boundary information lost; cross-session correlation degrades |
| `log_user_prompt.py` | observability | No metric impact | Prompt density invisible; gate-without-cause analysis impossible |
| `auto_attest_commit.py` | observability | No metric impact directly | Commit attestation chain breaks; author-filter (`--author-filter` metric, §10) becomes meaningless |
| `log_external_ingress.py` | observability | No metric impact | WebFetch/WebSearch ingress invisible; downstream claim-basis traceability lost |
| `attest_subagent_stop.py` | observability | No metric impact | Subagent completion invisible; parent cannot verify subagent claim envelope |
| `pre_compact_checkpoint.py` | observability | No metric impact | Pre-compression snapshot lost; context-compaction destroys evidence |
| `check_mcp_tool_call.py` | observability | No metric impact | Third-party MCP invocation invisible; trust-boundary diagnostic loss |

The pattern visible in Table 3: **the five blocking hooks contribute the metric; the seven observability hooks contribute the audit timeline.** Removing observability hooks does not move the coverage number, but it removes the contextual evidence a reviewer needs to interpret that number. A future controlled ablation (L2) will quantify "moderate" / "major" against the metric.

---

## §7 Comparative analysis

We compare the runtime-evidence stack against four adjacent frameworks frequently invoked when AI accountability is discussed. The comparison is not "Phionyx is better" — each framework targets a different consumer and a different problem. The comparison is **structural**: which framework, if any, answers the dogfood question — *can it govern the agent that builds the system?*

**Table 2.** *Structural comparison of agent-governance frameworks against the dogfood test.*

| Property | Phionyx runtime evidence | LangGraph [@langgraph_docs] | OpenAI Agents SDK [@openai_agents_sdk] | NeMo Guardrails [@nemo_guardrails] | Anthropic RSP [@anthropic_rsp] | NIST AI RMF [@nist_ai_rmf_1_2023] |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Per-turn signed envelope | yes (RGE v0.2) | no | no | no | no | no |
| Harness-binding hooks at agent-pair-programming level | yes (12 hooks) | no | no | no | no | no |
| Reviewer-runnable reproduction at row level | yes (Evidence Matrix) | partial | no | partial | no | no |
| Shared-trace contract across governance components | yes (ADR-0006) | within graph only | within session | within rails | n/a | n/a |
| Audit-chain replayability from artefacts alone | yes (Ed25519 chain) | partial (state log) | no | no | no | n/a |
| Framework-clause mapping with declared assessment signal | yes (Row Schema [@abak2026evidenceprotocol]) | no | no | no | partial | no |
| Self-audit script reproducible by external reviewer | yes (single command) | no | no | no | no | no |

### §7.1 LangGraph

LangGraph provides durable graph-shaped agent execution, with replayable state and built-in tracing. It does not specify an envelope schema at the trajectory granularity; the LangSmith trace surface is operator-facing and not designed for external reviewer replay without access to the operator's infrastructure. It does not provide harness-binding hooks for the agent-pair-programming case (LangGraph runs *as* the agent runtime; it is not a harness *around* an agent's development).

### §7.2 OpenAI Agents SDK

The OpenAI Agents SDK provides a hosted state model, function-calling primitives, and observability through OpenAI's dashboards. The replay surface is bounded by the operator's contract with OpenAI; an external reviewer cannot independently verify what the agent did from artefacts alone. It does not address the agent-pair-programming case.

### §7.3 NeMo Guardrails / Guardrails AI

These frameworks provide per-turn policy gates (rails). They are closer in spirit to Phionyx's `phionyx_response_gate` than the other entries in this table. They do not provide a per-turn signed envelope, do not specify a coverage metric for their own use in agent-pair-programming, and do not bind invocation at the harness level (they are invoked from within the agent's code, which makes their invocation again agent-mediated and probabilistic).

### §7.4 Anthropic Responsible Scaling Policy

The RSP is an organisational-policy artefact. It commits to capability evaluations, AI Safety Levels, and deployment protocols. It is the right shape of artefact for organisational accountability. It does not specify, and is not designed to specify, runtime artefacts that a developer can produce on a per-commit basis. It complements the protocol introduced here; it does not substitute for it.

### §7.5 NIST AI RMF / ISO/IEC 42001

NIST AI RMF 1.0 [@nist_ai_rmf_1_2023] and ISO/IEC 42001 [@iso_iec_42001_2023] are framework artefacts: they specify what obligations a trustworthy AI system should satisfy. They do not specify which executable artefacts satisfy which obligation. They are the consumers of the kind of evidence rows that paper_02 [@abak2026evidenceprotocol] introduces; they are not the producers.

### §7.6 Reading the table

No row of Table 2 says any other framework is *wrong*. Each is correct for its consumer. The reading of the table is: **none of the listed frameworks, individually or jointly, produces a reviewer-runnable, harness-bound, per-turn-signed evidence trail at the agent-pair-programming level**. That trail is what the Phionyx runtime-evidence stack adds.

---

## §8 Reviewer-runnable evidence

The reproducibility surface is the public repository at [github.com/halvrenofviryel/phionyx-research](https://github.com/halvrenofviryel/phionyx-research). All claims in this paper are pinned to commit `4bca5f3e` of the same.

**Public CI status.** The public reproduction at commit `c8fa1f9` on Python 3.12 reports `1131 passed, 7 skipped in 13.73s`. This is the canonical evidence table entry **T7** at `docs/arxiv/CANONICAL_EVIDENCE_TABLE.md` and the value cited in any external communication.

**Coverage measurement reproduction.**

```bash
git clone https://github.com/halvrenofviryel/phionyx-research
cd phionyx-research
git checkout 4bca5f3e
python3 scripts/active/runtime_evidence_self_audit.py --days 30
```

The output is written to `docs/strategic/runtime_evidence_self_audit_<DATE>.md`. Within the limit that the reviewer's clone may have a different telemetry archive (the telemetry is the dataset, the script is the deterministic transformation), the script's behaviour matches the reports cited in §6.

**Dashboard reproduction.**

```bash
cd apps/founder-console
npm install && npm run dev
# open http://localhost:3005/runtime-evidence
```

The dashboard renders the same numbers as the audit script, via `/api/runtime-evidence?days=30`.

**Architecture-constants reproduction.** From `docs/arxiv/CANONICAL_EVIDENCE_TABLE.md`: 46 pipeline blocks (A1), pipeline contract v3.8.0 (A2), CQS 0.862 (A3), 4 kill-switch triggers (A6), 4 ethics frameworks (A7).

---

## §9 Limitations

**L1. n=1 sample.** The case study is one codebase, one developer, one agent host (Claude Code), one 30-day window. Generalisability across codebases, developers, or agent hosts is not claimed and is named as future work.

**L2. Pre-intervention window dominance.** The 30-day window in §6.4 mostly pre-dates the intervention; the structural effect of the new blocking hooks is a forecast, not a measured outcome. The next audit cycle (≥ 7 days post-intervention, with 30-day rolling window) is the load-bearing test of the mechanism claim. We commit to publishing that audit when the window matures.

**L3. Conservative metric, by design.** The 2-per-commit denominator does not capture work the agent does outside commit boundaries (research, planning, dry runs). A more aggressive metric (e.g., 1 gate call per Edit) would catch more activity but would also penalise legitimate non-mutating work. The current metric is the honest minimum.

**L4. Strict mode is a deployer responsibility.** Blocking hooks escalate from WARN to BLOCK only when `PHIONYX_MCP_GATE_STRICT=1` is set. A deployer who runs without strict mode loses the binding property. This is the protocol's deployer-responsibility row (per the schema in [@abak2026evidenceprotocol]), not a workaround.

**L5. Hook coverage is partial.** The advisory CLAUDE.md text remains agent-mediated for any action the hooks do not cover (e.g., responding to a user question that doesn't reference a named artefact). We do not claim hooks eliminate the stochastic input gap entirely; they close it for the highest-value paths (commits, edits, agent spawn, external effects, question grounding).

**L6. Audit-script edge case.** The 2026-04-28 row in both audit reports shows 33 gate calls but 0 commits with 0.0% coverage (because the denominator is zero). This is a known interpretive caveat: an integration-test session emitted telemetry without git activity. The script could be modified to surface this case differently; it is left as-is because the surface form preserves the raw signal.

**L7. Input-quality assessment is out of scope.** Even when the gate is invoked, the assistant constructs the inputs (`action_type`, `evidence_count`, etc.). A future protocol layer can address whether the inputs themselves are faithful to the situation; this paper measures only invocation, not invocation quality.

**L8. The 100% ceiling is not achievable under the current design.** The denominator counts all commits in `git log` indiscriminately, including classes of commit that structurally bypass the Claude Code harness:

- **Founder direct commits.** Terminal commits made outside Claude Code emit no `PreToolUse:Bash` event; they enter the denominator but cannot enter the numerator.
- **Wrapper-script commits.** `make deploy`, `bash scripts/release.sh`, `python -c "subprocess.run(['git','commit'...])"` — the matcher regex `git commit|git push` runs against `$TOOL_INPUT`, which does not contain the literal substring in these cases.
- **Merge, rebase, cherry-pick.** `git merge`, `git rebase -m`, `git cherry-pick` all produce commits without matching the commit/push regex.
- **Automation traffic.** Pre-commit hooks that auto-fix and re-stage, CI-side commits, submodule updates — all increment commits without ever traversing the binding layer.

Even when these classes do not apply, the metric is stricter than the mechanism: the formula expects 2 gate calls per commit, while the hook is satisfied by ≥1 recent gate call within its recency window. A single gate call followed by four quick related commits passes the hook on all four but reads 12.5% in the formula. For the sole-developer Phionyx setup with the current matcher set, we estimate the realistic ceiling at **75–85%**, not 100%. Three near-term remediations are named in §10: aligning the metric with the mechanism, filtering the denominator by commit author, and the structural answer — conversation-envelope wrapping.

The response classes that produce *no* commit at all (research-only sessions, planning, pure conversation, reading + summarising) are not penalised by this metric — they neither raise nor lower it. They are also currently uncovered by any envelope; §10's conversation-envelope wrapping is the structural answer for them too.

---

## §10 Future work

> **2026-05-27 update.** Two items previously listed here have shipped in v0.7.2 (commit `2f6c0929`) and moved into §4.4 (hook 13–14) and §4.5 (subagent layer): (i) per-edit language-tool feedback into the assistant's same-turn observation surface, and (ii) a fresh-context adversarial diff-reviewer subagent. The remaining items below stay as future work because they require either a harness-contract change (conversation envelope wrapping) or a measurement-protocol extension (author-filtered denominator).

- **Conversation envelope wrapping (Katman C) — the structural answer to L8.** Every assistant turn produces an envelope automatically as a property of the harness contract, not of the agent's discretion. Coverage stops being a commit-bound metric and becomes a *turn coverage* — the fraction of assistant turns that carry a signed envelope. Under turn coverage, the response classes that L8 names as currently uncovered (research, planning, pure conversation, summarisation, founder-direct-commit reactions) all enter the metric on the same footing as a commit. The 100% ceiling becomes a hardware property of the harness, not a discipline property of the agent. Design phase; ADR pending.
- **Extended matcher set.** Extend the `PreToolUse:Bash` regex to cover wrapper-script patterns (`make .*deploy|publish|commit`, `bash scripts/.*\.sh`, `python.*subprocess.*git`) so that L8's wrapper-commit class enters the binding layer. Tractable; the matcher is data, not code.
- **Author-filtered denominator.** The `auto_attest_commit.py` hook already records the SHA of every Claude-initiated commit. The audit script can intersect `git log` against that SHA set so the denominator counts only commits the harness saw. The metric becomes a measurement of compliance on actually-bound commits, not a measurement diluted by direct-commit traffic the protocol never claimed to cover. Backwards-compatibility cost: an alternative metric series, not a replacement.
- **Metric–mechanism alignment.** Optional alternative: define a secondary coverage metric `C'(t) = |\mathrm{committed\_turns\_with\_recent\_gate}(t)| / |\mathrm{committed\_turns}(t)|` that matches the mechanism's recency window. Reported in parallel with the strict 2× metric so the comparison surface to §6 remains intact.
- **Multi-developer / multi-session aggregation.** The trace contract supports it; the audit script does not yet break down coverage per developer or per session.
- **Cross-host portability.** Would the same protocol bind under a different agent harness (Cursor, Zed, Aider)? Each harness exposes different hook surfaces. The Phionyx hook scripts are CLI-level — they should port, but porting is unverified.
- **Tighter coupling.** ADR-0006 names a v0.5 follow-up: server-MCP `flag_anomaly` ↔ pipeline block #23 (`behavioral_drift_detection`). The shared-trace contract unblocks the integration; the design has not been written.
- **Input-quality gating.** The second-order problem named in L7. A future protocol layer could require independent verification of the inputs to the gate, not just the gate's invocation.

---

## §11 Conclusion

We started with an obligation: Phionyx publishes a runtime-evidence discipline, so Phionyx's own AI-assisted development must demonstrate the same discipline. We defined the stochastic input generation gap as the mechanism by which advisory rules fail to bind probabilistic operators. We specified a reproducible coverage metric, measured a 7.5% baseline, documented an intervention layer of 12 harness hooks, and re-measured at 9.5% — knowing that the +2 percentage points is largely an artefact of the intervention session itself, not yet the structural effect.

The contribution is not the number. It is the discipline of publishing the number, with the mechanism that should move the number, with a falsifiable forecast for what the number will read in 30 days, and with a single command that any reviewer can run to independently verify the next reading.

This is what we mean when we say *runtime evidence*. AI accountability is not a slogan and not a promise; it is a path from a measured gap, through a deterministic mechanism, to a reproducible next measurement. The artefact in front of you is one instance of that path applied reflexively to its own author.

> If the next 30-day audit reports structurally higher coverage, this paper's mechanism claim is supported by data its own authors did not yet have when they wrote it. If it does not, the mechanism failed and we publish that, too. Both outcomes are the discipline.

---

## References

See `references.bib` (parallel file; extends `paper_02/references.bib` with case-study-specific cites).

---

## Appendix D — Companion artefacts (Phionyx runtime evidence programme)

This paper documents one instance — the Claude Code agent-pair-programming workflow — of a broader programme. The full Phionyx runtime evidence layer consists of seven ecosystem layers; each is a public artefact at a separately versioned and citable repository under [`github.com/halvrenofviryel`](https://github.com/halvrenofviryel). The same RGE v0.2 envelope semantics (§2.2, App. C) thread through all of them.

| Layer | Repository | Role in the evidence chain |
|---|---|---|
| Core SDK | `phionyx-research` / `phionyx-core` | 46-block pipeline, RGE v0.2 schema, signing primitives. Library that all other layers extend. |
| Standard | `phionyx-evaluation-standard` | Proposed evaluation profile — JSON schemas for reliability, safety, coherence, determinism dimensions. Vendor-independent assessment surface. |
| MCP inward (self-governance) | `phionyx-pipeline-mcp` | Agent self-claim verification: LLM declaration → `git diff` truth → physics gate. The MCP whose blocking + observability is measured in §6 of this paper. |
| MCP outward (trust boundary) | `phionyx-mcp-server` | Third-party MCP tool call signing, descriptor hashing, tamper-evident envelope chain. Defends against the Jamshidi et al. threat taxonomy. |
| Framework adapters | `phionyx_langchain_langgraph`, `phionyx_openai_agents` | Each chain / tool / LLM event + supervisor handoff becomes a signed envelope. Same chain semantics; different host runtimes. |
| Eval bridge | `phionyx-eval-inspect` | Read-only adapter converting Phionyx RGE chains into Inspect AI `.eval` log format. Replayable agent evaluations for reviewer-facing artefacts. |
| Reference application | `hearthos` | Bounded-authority pattern reference implementation — AI proposes, responsible adult executes. NOT a Phionyx Core production proof; a separate authority-pattern demonstration that motivates the Phionyx adapter target. |

The case study presented in §6 measures binding behaviour at the MCP-inward layer (self-governance MCP) under one host (Claude Code). Generalisation across the other layers — the second-host replication in §10's future work, the cross-framework portability in §7's comparison — is the path from this case study to platform claim. None of the other layers are evaluated here; their existence and architectural role are surfaced so a reviewer understands the position of this paper in the broader programme.

The reviewer can verify the existence and current state of each layer at the cited repository; each is AGPL-3.0, has at least one PyPI release, and points at the same RGE v0.2 envelope contract that this paper instruments.

---

## Appendix A — `.claude/settings.json` hook configuration (excerpt)

The committed, runtime-shared Claude Code settings at `4bca5f3e`:

```json
{
  "env": { "PHIONYX_MCP_GATE_STRICT": "1" },
  "hooks": {
    "SessionStart":      [{ "hooks": [{ "command": "python3 $CLAUDE_PROJECT_DIR/tools/claude_code_mcp/session_start_attest.py" }] }],
    "UserPromptSubmit":  [{ "hooks": [{ "command": "python3 $CLAUDE_PROJECT_DIR/tools/claude_code_mcp/log_user_prompt.py" }] }],
    "PreToolUse":        [
      { "matcher": "Bash",
        "hooks": [
          { "command": "if echo \"$TOOL_INPUT\" | grep -qE 'git commit|git push'; then python3 .../check_mcp_gate.py --mode pre-tool; fi" },
          { "command": "if echo \"$TOOL_INPUT\" | grep -qE 'gh pr|gh release|...|terraform apply'; then python3 .../check_bash_external_effect.py; fi" }
        ]
      },
      { "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [{ "command": "python3 .../check_edit_gate.py" }] },
      { "matcher": "Agent",
        "hooks": [{ "command": "python3 .../check_agent_spawn.py" }] },
      { "matcher": "mcp__.*",
        "hooks": [{ "command": "python3 .../check_mcp_tool_call.py" }] }
    ],
    "PostToolUse":       [
      { "matcher": "Bash",          "hooks": [{ "command": "if echo \"$TOOL_INPUT\" | grep -qE 'git commit'; then python3 .../auto_attest_commit.py; fi" }] },
      { "matcher": "WebFetch|WebSearch", "hooks": [{ "command": "python3 .../log_external_ingress.py" }] }
    ],
    "Stop":              [{ "hooks": [{ "command": "python3 .../check_question_grounding.py" }] }],
    "SubagentStop":      [{ "hooks": [{ "command": "python3 .../attest_subagent_stop.py" }] }],
    "PreCompact":        [{ "hooks": [{ "command": "python3 .../pre_compact_checkpoint.py" }] }]
  }
}
```

Paths abbreviated for layout; full content at `.claude/settings.json`. Strict mode is the production setting.

---

## Appendix B — Self-audit script output shape

The script writes to `docs/strategic/runtime_evidence_self_audit_<DATE>.md` with five sections:

1. **Headline.** Total commits, total gate calls, expected gate calls per CLAUDE.md, coverage percentage.
2. **Per-day breakdown.** A table with columns `Day | Commits | Gate calls | All mcp calls | Coverage`. Days with no activity in either dimension are omitted.
3. **Directive distribution.** A table counting each unique directive value across the window (`pass | reject | regenerate | rewrite | n/a | checkpoint | auto_attest | ok`).
4. **Honest reading.** A short prose paragraph that names the mechanism behind the observed pattern. The 2026-05-25 reading explicitly identifies the stochastic input generation gap.
5. **Reproduction.** The single command that produced the report.

The script's source is `scripts/active/runtime_evidence_self_audit.py`. Its only flag is `--days N` (default 30). Telemetry parsing is in `tools/claude_code_mcp/_telemetry.py`.

---

## Appendix C — Governed Response Envelope v0.2 field-by-field

See **Figure 5**.

![Figure 5 — RGE v0.2 envelope schema](figures/fig5_envelope_chain.md)

> **Figure 5.** RGE v0.2 envelope fields and the chain linkage that makes the audit trail tamper-evident. The protocol-level description is in [@abak2026evidenceprotocol] §4.3; this figure is the visual companion. *(Source: `figures/fig5_envelope_chain.md`.)*

The fields fall into four groups: identification (`trace_id`, `turn_index`, `producer`), input/output evidence (`user_text`, `tool_descriptor_hash`, `input_hash`, `output_hash`, `tool_permission_scope`), runtime decision (`decision`, `decision_reason`, `runtime_policy_basis`, `approval_state`, `anomaly_flag`, `descriptor_change_detected`), and integrity (`previous`, `current`, `signature`, `public_key`). The first three groups describe what happened; the integrity block makes the description tamper-evident.

A reviewer with the producer's public key can verify any chain from the persisted JSON alone, without operator access. This is the manifesto §5.1 commitment ("decisions are inspectable by a third party") expressed at the schema level.

---

**Verification footer.** Every numeric claim in this paper traces to one of:

- `docs/arxiv/CANONICAL_EVIDENCE_TABLE.md` (T7, A1–A7)
- `docs/strategic/runtime_evidence_self_audit_2026-05-25.md` (7.5%, 261, 39, 522)
- `docs/strategic/runtime_evidence_self_audit_2026-05-26.md` (9.5%, 269, 51, 538, 85.7%)
- `docs/strategic/test_scenarios_2026-05-26.md` (13/13 pre-restart)
- `docs/strategic/test_scenarios_2026-05-26_postrestart.md` (13/13 post-restart with C4 strengthening)
- `phionyx_core/contracts/telemetry/canonical_blocks_v3_8_0.json` (46 blocks, v3.8.0)
- Pinned git SHAs: `c03f4ebd` (current HEAD), `dcc0c52f`, `4bca5f3e`, `0d66e17d`, `af45aec1`, `c8fa1f9`

**Reproduction:**

```bash
git clone https://github.com/halvrenofviryel/phionyx-research
cd phionyx-research
git checkout c03f4ebd
python3 scripts/active/runtime_evidence_self_audit.py --days 30
python3 scripts/active/runtime_evidence_self_audit.py --days 30 --author-filter
python3 scripts/active/runtime_evidence_test_scenarios.py
```

Mind-loop stage declaration per `.claude/rules/agi-architecture.md`: **none — infrastructure**.
