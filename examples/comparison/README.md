# Phionyx vs LangChain / LlamaIndex

The most common question when Phionyx lands next to an existing LLM
stack: *do I have to choose between this and LangChain?* No. They
operate at different layers.

This directory shows the distinction in code, not just prose.

## The role distinction

| Concern | LangChain / LlamaIndex | Phionyx |
|---------|------------------------|---------|
| Primary job | **Orchestrate** the LLM call: prompt assembly, tool calls, retrieval, agent loops, memory recall. | **Govern** the LLM output: input safety gate, deterministic state, kill switch, ethics gate, tamper-evident audit. |
| Treats the LLM as | A reasoning engine. The model's output is the answer. | A noisy sensor. The model's output is a measurement, not the answer (Echoism Axiom 1). |
| Determinism | Non-deterministic by design (chain output mirrors model sampling). | Strict in the substrate (Φ, gates, audit hash); the LLM stage is the single declared `noisy_sensor`. |
| Default safety | Optional guardrails layered on top. | Mandatory gates that the agent cannot prompt-engineer past. |
| State | Conversation history, vector memory. | Structured state vector (A, V, H, Φ, entropy) + audit chain. |
| Composability | LangChain *can* be the producer; Phionyx wraps the result. | Phionyx *can* sit on top; the producer is interchangeable. |

In a sentence: **LangChain decides what the LLM says next. Phionyx
decides what the runtime does with what the LLM said.**

## What the wrap pattern looks like

A LangChain or LlamaIndex chain produces text. Phionyx takes that text
through input safety, computes a state vector, runs the kill switch and
ethics gate, attaches a tamper-evident envelope, and returns the
governed result. The producer is interchangeable — same wrap, different
upstream.

See [`with_orchestrator.py`](with_orchestrator.py) for a runnable
illustration. The script uses a `pretend_chain()` stand-in so you
don't need a LangChain or LlamaIndex install to run it; the comment
block at the top of the file shows the one-line swap to use the real
ones.

## When to reach for which

- **You're building an agent** and need tool selection, RAG over a
  corpus, and conversation memory → start with LangChain or
  LlamaIndex. They have first-class APIs for those.
- **You're shipping that agent into production** and need a runtime
  contract — kill switch, ethics gate, deterministic Φ, audit chain
  → wrap whatever the orchestrator returns in a Phionyx governance
  layer. The producer becomes `noisy_sensor` input to the symbolic
  layer.
- **You only need the substrate** (deterministic state, governance
  primitives, audit) — Phionyx alone is enough; the orchestrator
  layer is optional.

The two layers are orthogonal. The mistake is treating them as
competitors and picking only one.
