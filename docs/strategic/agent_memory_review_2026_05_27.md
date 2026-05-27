# Agent Memory Architecture Review — 2026-05-27

**Status:** Inspiration source for v0.7.1 (F-RM1 + F-MS1).
**Sources reviewed:**

1. **Paul Iusztin (@pauliusztin)** — *Designing Your Agents' Unified Memory (via Knowledge Graphs)* — X post 2026-05-26. Author of *LLM Engineer's Handbook* (Decoding ML). Architecture: one graph + three memory types (short / long / reasoning) + one ingestion pipeline (Extract → Resolution → Embed → Deduplicate). Default backing store: MongoDB.

2. **Akshay Pachaar (@akshay_pachaar)** — *Pydantic fixed my Agent's Memory* — X article 2026-05-26. Founder of Daily Dose of DS. Argument: knowledge-graph memory only works when the schema is defined upfront with typed entities + edges (Pydantic `EntityModel` / `EdgeModel` / `EntityEdgeSourceTarget`). Worked through Zep + 10/10/10 hard limit (max 10 entity types, 10 edge types, 10 fields per type) as a deliberate reasoning boundary.

Both authors share one thesis: **agent memory is a data-modelling problem, not a retrieval problem**. Vector RAG fails on multi-hop reasoning because the bridge facts don't share surface tokens with the query; only a typed knowledge graph traverses the chain. And the typed graph only works when the dev declares the schema before the LLM starts extracting.

---

## Compare to Phionyx + Claude Code memory today

| Dimension | Phionyx own memory | Claude Code session memory (auto-memory) | Iusztin / Pachaar approach |
|---|---|---|---|
| Storage | Audit chain (envelope JSONL files); contracts (Pydantic v4 schemas) | Markdown files + frontmatter (`MEMORY.md` index) | Unified knowledge graph (MongoDB / Neo4j / Zep) |
| Memory types | RGE v0.2 envelope (per-turn) + Schema 8 (memory_mutation_envelope) — recording, not knowledge | 4 types: user / project / feedback / reference (flat files, single-file-per-memory) | 3 types: short-term (live conv state) + long-term (durable graph) + reasoning (graph of traces) |
| Schema discipline | **Strong** — typed Pydantic v4 contracts (~23 contract tests), `additionalProperties: false`, RGE v0.2 + Schema 8/9 envelopes | **Weak** — frontmatter has `name` / `description` / `type` (4 fixed values) but body is free-text; no length bound; no validation hook | **Strong** — Pydantic `EntityModel` + `EdgeModel`, 10/10/10 hard limit |
| Cross-references | `runtime_policy_basis[]`, `evidence_links[]`, `previous` hash chain | Manual `[[name]]` Markdown links | Auto-extracted typed edges between graph nodes |
| Retrieval | `verify_chain_integrity`, `query_audit_history` — chain-walk; no knowledge query | "Claude reads `MEMORY.md` index, navigates by topic" — RAG-like by hand | Graph traversal (multi-hop): `Alice → manages → Project Atlas → runs_on → PostgreSQL` |
| Reasoning memory ("what worked before?") | **Data exists** in gate-call telemetry: `response_gate` directives + reasons; `verify_claim` evidence types + outcomes; `causal_trace` chains. **No query layer.** | Manually written `feedback_*.md` files; founder edits by hand | Stored as graph; agent queries its own history ("which decisions succeeded?", "which reasoning paths worked?") |
| Resolution / deduplication | None at content level — every envelope is new | None — founder manually consolidates | Pipeline step: Extract → Resolution → Dedup; nightly re-process |
| Temporal handling | Envelope `timestamp_utc` + hash-chain order | `Last verified:` field, manually maintained | Per-edge validity windows |
| Audit integrity | **Strong** — Ed25519 signatures + SHA-256 chain | None — git history only | None native to the memory layer |

**The key observation:** Phionyx and the Iusztin/Pachaar approaches address **orthogonal concerns**, not the same problem.

- Phionyx audits **what the agent did** (turn-level, per-decision, signed).
- Iusztin / Pachaar designs **what the agent knows** (entity-level, durable, queryable).

Phionyx already applies strict schema discipline to its evidence envelopes. It does **not** apply the same discipline to its own session-memory / reasoning-memory layers. That is the gap v0.7.1 closes.

---

## What's reusable, what's not

### Reusable

1. **Pydantic-typed memory entries.** Akshay's `EntityModel` + `EdgeModel` pattern is exactly what Phionyx already does for its evidence envelopes. Applying it to the Claude Code auto-memory frontmatter is a pure-win symmetry.

2. **Reasoning memory as a queryable view over existing data.** Iusztin's "what worked before?" memory type maps directly to data Phionyx already collects: every `phionyx_response_gate` directive is a "decision succeeded / failed" record; every `phionyx_verify_claim` is a "what evidence was offered, was it accepted" record. The data is in `data/mcp_telemetry/session_*.json` today; F-RM1 builds the typed graph view.

3. **The 10/10/10 hard-limit philosophy.** Zep's `≤ 10 entity types, ≤ 10 edge types, ≤ 10 fields per type` constraint is a *reasoning boundary*, not an arbitrary number — it forces the dev to model what matters. F-MS1 adopts an analogous discipline for Claude Code memory frontmatter (5 fixed types, 5 required fields, length bounds).

### Not reusable

1. **MongoDB / Neo4j in Phionyx Core.** CLAUDE.md `.claude/rules/core-boundary.md` is unambiguous: Phionyx Core depends only on stdlib + Pydantic + internal modules. Any graph DB lives in a companion package (`phionyx-memory-graph`?) or in a downstream consumer's deployment — never in Core.

2. **Replacing Markdown memory files with graph nodes.** The Markdown auto-memory directory is human-editable, git-diff-friendly, and grep-able. Migrating to a binary graph DB would lose all three. The right move is to *validate* the Markdown frontmatter against a Pydantic schema — keep Markdown as the source of truth.

3. **"Agent memory = AGI progress" framing.** `.claude/rules/agi-architecture.md` Invariant 3 is explicit: retrieval-only changes are NOT AGI progress. F-RM1 is a query-view over recorded data — automation / governance improvement, not cognitive advance. The roadmap entry labels this correctly.

---

## v0.7.1 features that land from this review

### F-RM1 — Reasoning Memory Graph

A typed Pydantic graph view over `data/mcp_telemetry/session_*.json` + `data/mcp_envelopes/<trace>/` (existing telemetry, no new collection). Nodes: `claim`, `verdict`, `commit`, `evidence_type`, `outcome`. Edges: `produced_verdict`, `had_evidence_type`, `led_to_commit`, `was_blocked_by`, `triggered_revision`. A Founder Console panel at `/runtime-evidence/reasoning-graph` (extends the existing `/runtime-evidence` page) renders ≥ 4 canonical multi-hop queries:

- *"Which `evidence_type` most often produces a `pass` verdict?"* — `evidence_type → had_evidence_type → claim → produced_verdict → verdict`
- *"Which commits got the most `regenerate` directives?"* — `verdict → triggered_revision → claim → led_to_commit → commit`
- *"Which claims passed despite low evidence_count?"* — filter on claim attributes + verdict outcome
- *"What's the lag between `verify_claim` and `response_gate` per session?"* — temporal traversal

### F-MS1 — Memory Schema Validation

A Pydantic model `MemoryFrontmatter` (in `tools/claude_code_mcp/memory_schema.py`) plus a pre-commit hook (`tools/claude_code_mcp/check_memory_schema.py`) that validates every file under `/home/toygar/.claude/projects/-mnt-data-claude-phionyx/memory/`. Required frontmatter fields: `name` (kebab-case slug), `description` (≤ 200 chars), `type` (enum: user / feedback / project / reference / reasoning_lesson — the fifth type added by F-MS1), `linked` (optional list of `[[name]]` slugs), `last_verified` (ISO-8601 date for project / reference / reasoning_lesson types). Body bounds: ≥ 5 lines, ≤ 200 lines. Failing files break the pre-commit hook with a clear remediation hint.

---

## What this review does NOT recommend

- **A new memory framework.** Zep / mem0 / Letta exist; Phionyx is not in that market. Phionyx is the **audit layer** *above* memory frameworks (per Schema 8 / phionyx-letta). This review reaffirms that boundary.

- **Knowledge-graph migration for Phionyx core memory.** Out of scope; would violate core-boundary rules and lose human-editability of the markdown layer.

- **AGI claims.** Both features are infrastructure / discipline improvements. Mind-loop stage: none. `agi-architecture.md` Invariant 3 explicitly applies.

---

## Discipline note

This document follows `feedback_verify_state_before_asserting.md`: every numeric claim about current Phionyx state (file paths, schema fields, memory type counts, contract test counts) was verified this turn against the actual repo (`tools/phionyx_compliance/`, `phionyx_core/contracts/`, `~/.claude/projects/-mnt-data-claude-phionyx/memory/`). If a claim turns out stale, the document — not the recorded state — is wrong.
