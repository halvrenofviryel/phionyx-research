# Phionyx vs. Agent / LLM Orchestration Frameworks

> **Last verified:** 2026-05-06 against Phionyx Core SDK v0.3.0
> **Audience:** developers and technical reviewers asking *"How does Phionyx fit alongside / against [LangChain | LlamaIndex | LangGraph | AutoGen | OpenAI Agents SDK | Guardrails]?"*

---

## TL;DR

Phionyx is **not an agent framework** and **not an LLM orchestrator**. It is a **runtime governance layer** that wraps any orchestrator's output and produces signed, reproducible, gate-checked turn-by-turn evidence.

The mental model is the same regardless of which framework you bring to the table:

```
[ Your LangChain / LlamaIndex / LangGraph / AutoGen /
  OpenAI Agents SDK / Guardrails / custom orchestrator ]
        │
        │  produces a candidate response and/or proposed tool call
        ▼
[ Phionyx governance path ]
        │
        │  input safety  →  state update  →  ethics gates
        │  →  kill switch  →  capability check  →  revision gate
        │  →  signed audit envelope
        ▼
       Released response (or refusal, with audit record)
```

In every comparison below the rule of thumb is:

> **Phionyx does not replace the framework. It wraps the framework's output.**

---

## Comparison matrix

| Capability | LangChain | LlamaIndex | LangGraph | AutoGen | OpenAI Agents SDK | Guardrails AI | **Phionyx** |
|---|---|---|---|---|---|---|---|
| Prompt / chain orchestration | ✅ Core | Partial | ✅ Core | ✅ Multi-agent core | ✅ Core | ❌ | ❌ |
| Retrieval / RAG | ✅ | ✅ Core | Via tools | Via tools | Via tools | ❌ | ❌ |
| Multi-agent / graph control | Partial | ❌ | ✅ Core | ✅ Core | Partial | ❌ | ❌ |
| Tool calling | ✅ | ✅ | ✅ | ✅ | ✅ | Partial | Gates calls — does not originate them |
| Output schema validation | Partial | Partial | Partial | Partial | Partial | ✅ Core | Partial (envelope schema) |
| **Pre-response safety gate (kill-switch / fail-closed)** | ❌ | ❌ | ❌ | ❌ | ❌ | Partial (validation rules) | ✅ Core |
| **Per-turn signed audit chain** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Core (Ed25519) |
| **Capability-bounded action surface** | ❌ | ❌ | Partial (graph nodes) | Partial (agent roles) | Partial (tool whitelist) | ❌ | ✅ Core (CapabilityProfile) |
| **Behavioural drift detection across turns** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Core (block 23) |
| **Standards-evidence mappings** (OWASP / EU AI Act / NIST) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Core (`docs/mappings/`) |
| LLM provider neutrality | ✅ | ✅ | ✅ | ✅ | OpenAI-first | ✅ | ✅ (LLM-as-sensor; provider-agnostic) |
| License | MIT | MIT | MIT | MIT | MIT-equivalent | Apache-2.0 | AGPL-3.0 + commercial |

✅ = first-class concept · Partial = present but not central · ❌ = not in scope

The **bottom four "Phionyx core" rows** are the rows where Phionyx genuinely adds something none of the other frameworks claim. The first six rows are where Phionyx is *deliberately silent*: building those into Phionyx would be reinventing the orchestrator.

---

## Per-framework deep dive

### vs. LangChain

**What LangChain does:** chains, prompts, retrievers, tool calling, output parsers, model-provider abstraction.
**What Phionyx adds:** governance path around what the LangChain chain produces.
**Relationship:** *wrapper*. Your existing `RunnableSequence` stays as-is; Phionyx wraps the chain's output in a governed envelope.
**When you want both:** when your LangChain agent calls tools that have side effects (file write, email, transfer) — Phionyx gates the proposal *before* the side-effect surface is reached.
**Worked example:** [`examples/comparison/with_orchestrator.py`](../../examples/comparison/with_orchestrator.py).
**Standards-relevant signal:** OWASP Agentic AI T1, T2, T6 attacks against an unguarded LangChain agent are blocked at Phionyx's input safety gate or kill switch. See `examples/adversarial/prompt_injection_tool_call.py`.

### vs. LlamaIndex

**What LlamaIndex does:** retrieval, embedding-indexed memory, RAG pipelines, query engines.
**What Phionyx adds:** runtime governance over what the query engine returns and proposes.
**Relationship:** *wrapper + retrieval-side gate*. LlamaIndex retrieves; Phionyx's input-safety gate inspects the retrieved context as well as the user prompt before the LLM is invoked. (Memory poisoning — OWASP T1 — is a relevant attack class here.)
**Phionyx-internal note:** UKIPO patent SF3 (GB2609504.2) covers an embedding-indexed memory store with impact-weighted cache eviction. The IP and LlamaIndex are *complementary*, not competitive — Phionyx does not provide retrieval; it provides governance around retrieved context.

### vs. LangGraph

**What LangGraph does:** stateful, graph-based agent control flow on top of LangChain.
**What Phionyx adds:** per-node governance evidence + cross-turn drift detection.
**Relationship:** *wrapper at node boundaries*. Each LangGraph node's output passes through `govern()`. Phionyx's behavioural drift detection (canonical block 23) operates *across* nodes, which LangGraph itself does not provide.
**When you want both:** multi-step agents where you need a per-step audit record and a system-level drift signal. LangGraph gives you the control flow; Phionyx gives you the governance evidence per step.
**Demo (planned):** `examples/integrations/langgraph/` — single graph node + Phionyx wrapper round-trip.

### vs. AutoGen

**What AutoGen does:** multi-agent conversation, role-based agents, group chat patterns.
**What Phionyx adds:** governance evidence at each agent's response.
**Relationship:** *per-agent wrapper*. Each AutoGen agent's response is a separate `govern()` turn. Cross-agent reasoning collusion (OWASP T6 / T7 territory) becomes auditable when each agent's release is gated and logged.
**Caveat:** AutoGen integration is **deferred** in the Phionyx roadmap (master plan v2.0 P2-deferred); LangGraph + OpenAI Agents SDK are sufficient demo coverage for the agentic-AI surface.

### vs. OpenAI Agents SDK

**What the OpenAI Agents SDK does:** OpenAI-native agent loop with tools, hand-offs, tracing.
**What Phionyx adds:** provider-agnostic, signed-audit, fail-closed governance layer.
**Relationship:** *wrapper at agent-loop boundary*. The OpenAI Agents SDK has its own tracing — Phionyx's audit chain is *additional* and *signed* (Ed25519). Useful when the deployer needs reproducible audit evidence (e.g., for EU AI Act Article 12) that does not depend on the model vendor's tracing infrastructure.
**Demo (planned):** `examples/integrations/openai-agents/` — agent loop turn + Phionyx wrapper.

### vs. Guardrails AI

**What Guardrails does:** structured-output validation, schema enforcement, retry on validation failure.
**What Phionyx adds:** runtime safety gates that operate independently of output schema validation.
**Relationship:** *complementary, not competing*. Guardrails enforces *what the response must look like*. Phionyx enforces *whether the response should be released at all* (kill switch, ethics gate). Both can run on the same turn — Guardrails on the output shape, Phionyx on the release decision and audit evidence.
**Worth noting:** Guardrails AI publishes "AI Validators"; Phionyx publishes "AI Governance Mappings". Different artefact classes, useful together.

---

## When to use Phionyx (and when NOT)

### Use Phionyx when

- You need **reproducible evidence** that a specific governance decision was applied to a specific turn (deployer audit, regulator inquiry, EU AI Act Article 12 obligation).
- You need a **fail-closed kill switch** that is independent of the LLM provider's safety classifier.
- You need **per-turn signed audit records** that survive the model vendor's infrastructure.
- You need a **capability-bounded action surface** documented as a contract, not as a prompt-engineering convention.
- You need to map runtime artefacts to standards (OWASP / EU AI Act / NIST) with **deployer-responsibility** lines on every row.

### Do NOT use Phionyx for

- LLM **prompt engineering** or chain orchestration — use LangChain / LlamaIndex / your own.
- **Retrieval / RAG / vector-store engineering** — use LlamaIndex / Pinecone / Chroma.
- **Multi-agent control flow** — use LangGraph / AutoGen.
- **Model fine-tuning, training-data governance, or fairness measurement** — out of architectural scope (EU AI Act Article 10 is an explicit `Gap` in our mapping).
- **Compliance certification** — Phionyx produces evidence inputs; certification is granted only by accredited bodies. See `docs/mappings/` "What this is not".

---

## "Can I use Phionyx without giving up my framework?"

Yes. The wrapper pattern is identical across all six frameworks. The minimal change is replacing this:

```python
response = my_framework.run(prompt)
return response
```

with this:

```python
envelope = govern(prompt, producer=my_framework.run, ...)
return envelope["response"]["text"] if envelope["governance"]["decision"] == "released" else None
```

The framework you bring stays as-is. The *only* thing that changes is whether the response is released to the user, and whether an audit record is produced.

---

## Licensing differences (read carefully)

| Framework | License | Phionyx implication |
|-----------|---------|---------------------|
| LangChain / LlamaIndex / LangGraph / AutoGen / OpenAI Agents SDK | MIT or MIT-equivalent | No license-level conflict with running Phionyx alongside |
| Guardrails AI | Apache-2.0 | No conflict |
| **Phionyx Core SDK** | **AGPL-3.0** + commercial | If you modify Phionyx, your modifications must be released under AGPL-3.0; if you run Phionyx as a network service, the network user has the right to receive the source. The patent grant is **not** included in AGPL-3.0 — patent rights are retained. See [`PATENT_NOTICE.md`](https://github.com/halvrenofviryel/phionyx-research/blob/main/PATENT_NOTICE.md). |

Wrapping Phionyx around a non-AGPL framework does **not** force the framework to become AGPL — only Phionyx's own code is governed by AGPL-3.0. The framework remains under its original license.

---

## Standards-evidence dimension (the load-bearing differentiator)

Phionyx publishes **three evidence mappings** none of the other frameworks publish:

- [OWASP Agentic AI Threats v1.0](../mappings/owasp-agentic-ai-2025.md) — 15 threats, 1 Full / 10 Partial / 4 Gap.
- [EU AI Act Articles 9–15](../mappings/eu-ai-act.md) — 1 Full (Article 12 = AuditRecord v4) / 1 Gap (Article 10 = training-data governance) / 5 Partial.
- [NIST AI RMF 1.0](../mappings/nist-ai-rmf.md) — 1 Full (MANAGE) / 3 Partial within the runtime perimeter.

Plus a [JSON Schema (Draft 2020-12)](../mappings/schema/) for the row format itself, so other projects can adopt the same evidence-mapping contract.

If you are a deployer asked *"where is your evidence for [Article X / Function Y / Threat Z]?"* — Phionyx is the only framework on this comparison list whose answer points at a specific runtime mechanism, a reproducible test, and an explicit deployer-responsibility line.

---

## Honest limitations of this comparison

- This document compares **frameworks at a conceptual level**. Each framework has integrations and extensions Phionyx does not benchmark against.
- Capability matrix rows reflect **public claims as of the verification date above**. Frameworks evolve; verify against the framework's current docs before commitment.
- Phionyx's "Core" rows are **self-assessed** against the standards-evidence mapping criteria. Independent review would tighten the labels (this is on the Phase 4 roadmap).
- Phionyx does **not** claim to replace any of the listed frameworks. The comparison is positioning, not competition.

---

## Cross-references

- Worked wrapper example: [`examples/comparison/with_orchestrator.py`](../../examples/comparison/with_orchestrator.py)
- Adversarial scenarios (orchestrator-relevant): [`examples/adversarial/`](../../examples/adversarial/)
- Side-by-side harness (with vs without Phionyx governance): [`examples/before_after/`](../../examples/before_after/)
- Standards mappings: [`docs/mappings/`](../mappings/)
- Mapping JSON Schema: [`docs/mappings/schema/`](../mappings/schema/)
- Architecture paper: arXiv submission pending (cs.AI primary, cs.SE secondary; Zenodo concept DOI [10.5281/zenodo.20027534](https://doi.org/10.5281/zenodo.20027534))

---

> **Document discipline:** Each capability claim above can be challenged with a specific PR. If you find a row inaccurate against the *current* version of a framework, please open an issue with `docs(comparison)` label — the matrix is meant to be falsifiable, not promotional.
