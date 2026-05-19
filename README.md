# Phionyx Core SDK

**Phionyx treats LLM output as a noisy sensor measurement, not as truth.**

A deterministic AI runtime that maps every model output through 46 evaluation blocks before allowing it to affect system behavior. Signed audit trails, replayable decisions, and reviewer-runnable governance evidence — not better prompts, a control system around an unreliable sensor.

Beyond governance, Phionyx Core ships a **physics module** that produces deterministic coherence telemetry over a structured state vector — useful for NPC/agent drift detection, session-level coherence tracking, and reproducible runtime evaluation.

[![CI](https://github.com/halvrenofviryel/phionyx-research/actions/workflows/ci.yml/badge.svg)](https://github.com/halvrenofviryel/phionyx-research/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/phionyx-core.svg)](https://pypi.org/project/phionyx-core/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-1%2C131%20pass%20%2F%207%20skip-brightgreen.svg)](tests/)
[![Mypy](https://img.shields.io/badge/mypy-strict%20%7C%200%20errors-brightgreen.svg)](.github/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20027534.svg)](https://doi.org/10.5281/zenodo.20027534)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--3718--4010-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0009-0002-3718-4010)
[![Substack](https://img.shields.io/badge/Substack-Deterministic%20AI%20Engineering-FF6719?logo=substack&logoColor=white)](https://phionyxresearch.substack.com)
[![Discussions](https://img.shields.io/github/discussions/halvrenofviryel/phionyx-research?logo=github&color=5e60ce)](https://github.com/halvrenofviryel/phionyx-research/discussions)

```bash
pip install phionyx-core
python -c "import phionyx_core; print('Phionyx Core ready —', phionyx_core.__version__)"
```

Or one command end-to-end (fresh venv → install → smoke flow):

```bash
bash <(curl -sSL https://raw.githubusercontent.com/halvrenofviryel/phionyx-research/main/scripts/demo.sh)
```

Most AI frameworks let the LLM decide. Phionyx doesn't. Every LLM response passes through a 46-block deterministic pipeline with safety gates, ethics checks, and physics-based state tracking — before it reaches the user.

The substrate is demonstrable in seconds **without an LLM, server, or API key** — see the [demo table](#try-it-in-30-seconds) below.

> 📖 **The project explained as a series:** [Deterministic AI Engineering on Substack](https://phionyxresearch.substack.com) — four essays on the design choices behind this repo. Latest: [*Treating LLMs as Sensors, Not Oracles*](https://phionyxresearch.substack.com/p/the-phionyx-architecture-treating) (2026-05-09).

---

## What Makes This Different

| Feature | Typical LLM Framework | Phionyx |
|---------|----------------------|---------|
| LLM role | Decision maker | Sensor (output is measurement, not truth) |
| Response control | Post-hoc filtering | Pre-response governance (46-block pipeline) |
| State tracking | Stateless or conversation history | Structured state vector (A, V, H, phi, entropy) |
| Safety | Optional guardrails | Mandatory gates (kill switch, ethics, HITL) |
| Determinism | Non-deterministic | Reproducible cognitive path |
| Memory | RAG / vector search | Impact-weighted semantic time eviction |

---

## Try It In 30 Seconds

**Three demo notebooks + a FastAPI wrapper. No API key. Runs locally.**

The substrate (state vector, Φ, governance gates, pipeline) is demonstrable
without an LLM, server, or external account. Each demo runs end-to-end and
embeds its outputs.

| # | Demo | Shows | Run time | API key |
|---|------|-------|----------|---------|
| 01 | [Determinism and Physics](examples/notebooks/01_determinism_and_physics.ipynb) | `EchoState2`, `calculate_phi_v2_1`, 1000-run determinism proof, valence × arousal Φ heatmap, side-by-side with a noisy alternative | ~30 s | No |
| 02 | [Kill Switch in Action](examples/notebooks/02_kill_switch_in_action.ipynb) | `KillSwitch` with 4 triggers + NaN fail-closed guard, tamper-evident event log | ~5 s | No |
| 03 | [Pipeline Blocks and Audit](examples/notebooks/03_pipeline_blocks_and_audit.ipynb) | Canonical 46-block pipeline (v3.8.0), custom `PipelineBlock` subclass, 100-run determinism | ~5 s | No |
| 04 | [FastAPI wrapper](examples/fastapi/) | HTTP `/govern` endpoint over the governance pipeline | <1 min | No |

Notebook 01 sweeps the cognitive component of Φ across the full Circumplex
(valence × arousal). The surface is smooth, bounded, and reproducible —
no LLM is involved at this layer.

![Phi cognitive across valence × arousal](docs/img/phi_heatmap.png)

```bash
pip install phionyx-core jupyter matplotlib
git clone https://github.com/halvrenofviryel/phionyx-research.git
jupyter notebook phionyx-research/examples/notebooks/
```

(Cloning is only needed because the notebooks live in the repo, not the
package. Source-only install is also supported — see
[`INSTALLATION.md`](INSTALLATION.md).)

---

## Quick Start — Full Runtime

For the LLM-backed orchestrator (governed response, state metrics, audit
trail):

```python
from phionyx_core import EchoOrchestrator, OrchestratorServices

services = OrchestratorServices()
orchestrator = EchoOrchestrator(services=services)

result = await orchestrator.run(
    user_input="How can I improve my study habits?",
    mode="edu",
    current_amplitude=5.0,
    current_entropy=0.3
)
# Returns: governed response + state metrics + audit trail
```

See [`examples/fastapi/`](examples/fastapi/) for an HTTP endpoint wrapper.

---

## Scope: what Phionyx is, and is not

Phionyx is an **early, working reference implementation** for deterministic
runtime governance. To keep claims aligned with evidence, here is what we
**do not** assert:

- **Phionyx does not make LLMs deterministic.** Model output stays probabilistic. Phionyx makes the *governance path* — gates, state, audit — deterministic.
- **Phionyx is not a certification authority.** The Evaluation Standard v0.1 is an *open evaluation profile*, not an accredited certification scheme.
- **Phionyx does not replace NIST AI RMF, ISO/IEC 42001, or the EU AI Act.** It is a runtime layer designed to *produce evidence* that maps onto those frameworks; it does not implement them on your behalf.
- **Current benchmarks are controlled reference benchmarks**, not third-party audits. Reproducible from this repo, but not yet independently validated.
- **Production-readiness is scoped to the demos in `examples/`**. The runtime is research-grade until pilot deployments and an external review land.
- **Clinical, medical, or psychological framings are out of scope** unless separately validated under the appropriate regulatory regime.

If a claim above feels too cautious for your context, write to founder@phionyx.ai — we will tell you what we have, what we do not, and what is on the roadmap.

### Known limitations

The following are real, not rhetorical. Treat them as load-bearing context when evaluating the project:

- **Benchmarks are controlled reference benchmarks**, not third-party audits. Determinism, cache eviction and CPU overhead figures are reproducible from this repository on a clean clone; they have not yet been independently re-run.
- **No third-party security review yet.** A paid independent review is on the roadmap; until it lands, treat the audit-trail and kill-switch implementations as research-grade.
- **No production deployment claims.** Phionyx has not been operated in a regulated environment. Use it as a reference and pilot artifact, not as a certified runtime.
- **LLM output quality is not guaranteed.** Phionyx governs *what reaches the user* (state, gates, audit) — it does not improve the model's own reasoning, hallucination rate, or domain accuracy.
- **Compliance mappings (planned) are evidence mappings, not legal certification.** Tracing artifacts onto NIST AI RMF / EU AI Act / ISO 42001 produces inputs that an auditor or compliance officer can use; it does not constitute legal compliance on its own.
- **The Φ (cognitive coherence) and entropy metrics are experimental.** They are useful as internal control signals and reproducible across runs, but they are not yet externally validated against established psychometric or behavioural benchmarks.

---

## Architecture

Phionyx implements three integrated layers:

**Layer 1 — Deterministic Cognitive Kernel**
- 46-block canonical pipeline (contract v3.8.0)
- Structured state vector: arousal, valence, entropy, time
- Hybrid Resonance Model for cognitive quality (Phi)
- Response revision gate: `pass | damp | rewrite | regenerate | reject`

**Layer 2 — Safety & Governance**
- 4-gate pre-response control (Outbound, Merge, Release, Data)
- Kill switch with 4 triggers (fail-closed)
- Deliberative ethics engine (4-framework reasoning)
- Human-in-the-loop queue with priority and expiry
- Ed25519-signed audit trail with hash chains

**Layer 3 — Semantic Time Memory**
- Impact-weighted cache eviction (+24% vs LRU, +72% vs FIFO)
- Monotonic semantic clock (t_local, t_global)
- Phi-decay for memory relevance

---

## Core Concepts

### State Vector

Every interaction maintains a structured state:

```python
from phionyx_core import EchoState2

state = EchoState2(
    A=0.5,       # Arousal (0.0-1.0)
    V=0.0,       # Valence (-1.0 to 1.0)
    H=0.3,       # Entropy (0.0-1.0)
    dA=0.0,      # Arousal derivative
    dV=0.0,      # Valence derivative
    t_local=0.0, # Semantic time (local)
    t_global=0.0 # Semantic time (global)
)
```

### Pipeline Blocks

```python
from phionyx_core.contracts.telemetry import get_canonical_blocks

blocks = get_canonical_blocks()  # 46 blocks (v3.8.0)
```

### Profiles

```python
from phionyx_core import ProfileManager

manager = ProfileManager()
profile = manager.load_profile("edu")  # or "game", "clinical"
```

---

## Testing

The public SDK ships with a verifiable subset that runs against a
clean `pip install phionyx-core` clone. CI enforces this on every push
across Python 3.10–3.13.

```bash
pytest tests/core tests/contract tests/benchmarks
# Public CI on commit c8fa1f9 (Python 3.12): 1,131 pass / 7 skip / 0 fail
```

> The historical / internal corpus across the internal development history (which
> includes integration tests, behavioural eval suites, and apps) is
> larger (~2,500+ checks). Only the figures runnable from this public
> repository on a clean clone are reported here as load-bearing claims.

---

## Reproducibility Pack (v0.3.0+)

Every tagged release attaches a small (< 1 MB) `reproducibility_pack_v*.zip`
containing JUnit XML, coverage XML, determinism hashes, benchmark JSON, the
canonical governed-response envelope, an audit-chain example, and an
OpenTelemetry sample trace. Build the same artifacts locally:

```bash
pip install -e ".[dev]"
python scripts/make_reproducibility_pack.py --zip
ls dist/reproducibility_pack_v*.zip
```

The pack is the artifact that backs every load-bearing claim on
[phionyx.ai/evidence](https://phionyx.ai/evidence). Reviewers do not have
to trust prose: the pack itself is the evidence.

---

## Evaluation Standard

Phionyx systems are evaluated against the [Phionyx Evaluation Standard v0.1](https://github.com/halvrenofviryel/phionyx-evaluation-standard):

- **Determinism Grading (D0-D3):** Non-deterministic to fully deterministic
- **Evaluation Levels (L0-L3):** Unmeasured to governance-grade
- **Composite Quality Score (CQS):** Multi-dimensional behavioral quality metric

---

## MCP companion packages — runtime evidence over Claude Code

Three sibling packages extend the Phionyx runtime into an end-to-end evidence stack for AI coding agents (Claude Code, Cursor, Zed, VS Code, JetBrains — any MCP-capable host):

- **[`phionyx-mcp-server`](https://github.com/halvrenofviryel/phionyx-mcp-server)** — *outward-facing layer.* MCP trust boundary governance: hashes tool descriptors at first observation, detects post-approval drift, signs every third-party tool call as a Reasoned Governance Envelope (RGE v0.2), and maintains a tamper-evident hash chain. Threat surface aligned with arXiv:2512.06556 (Jamshidi et al.) — tool poisoning, shadowing, rug pulls.
- **[`phionyx-pipeline-mcp`](https://github.com/halvrenofviryel/phionyx-pipeline-mcp)** — *inward-facing layer.* Self-governance gate over the agent's own *"I fixed this / I tested that / this code path changed"* declarations. Three-layer verification: LLM declaration → `git diff` truth → deterministic physics gate (a 9-block composition from the 46-block runtime). Returns a directive: `pass | regenerate | reject`.
- **[`phionyx-eval-inspect`](https://github.com/halvrenofviryel/phionyx-eval-inspect)** — *interoperability bridge.* Convert a Phionyx envelope chain into an [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) `.eval` log so Phionyx-governed runs are natively viewable in Inspect's tooling. Companion to the two MCP servers above; lets evaluation workflows consume Phionyx evidence without endorsement or partnership claims.

When the MCP servers are installed and registered with the same Claude Code host, they share a single `trace_id` per session (via `PHIONYX_TRACE_ID` env var with `~/.phionyx/active_trace` file fallback). One Claude Code conversation = one trace = end-to-end view of every third-party MCP tool call AND every agent self-claim gate decision. The Inspect bridge then converts that chain into the framework many eval teams already use.

```bash
# Install both MCPs (governance for live sessions):
pip install phionyx-pipeline-mcp[mcp-server-integration]

# Plus the Inspect AI bridge (post-session evaluation surface):
pip install phionyx-eval-inspect
```

The integration contract is documented in each repo; the trace coordination module is **read-only across the package boundary** — no cross-package write coupling.

---

## Compliance mappings

Phionyx publishes **evidence mappings** — not certifications — connecting runtime artifacts to industry threat models and risk frameworks:

- [`docs/mappings/owasp-agentic-ai-2025.md`](docs/mappings/owasp-agentic-ai-2025.md) — OWASP Agentic AI Threats v1.0 (15 categories, 1 Full / 10 Partial / 4 Gap)
- [`docs/mappings/eu-ai-act.md`](docs/mappings/eu-ai-act.md) — EU AI Act Articles 9–15 high-risk obligations (1 Full / 5 Partial / 1 Gap, with explicit deployer-responsibility per article)
- [`docs/mappings/nist-ai-rmf.md`](docs/mappings/nist-ai-rmf.md) — NIST AI RMF 1.0 four functions (Govern / Map / Measure / Manage; 1 Full / 3 Partial within the runtime perimeter, with explicit deployer-responsibility per function)
- [`docs/mappings/iso-42001.md`](docs/mappings/iso-42001.md) — ISO/IEC 42001:2023 AI Management System — 15 control-type rows (1 Full / 8 Partial / 6 Gap) **draft**; Annex A identifier accuracy requires paid-text verification

Each row is structured: framework description → Phionyx mechanism → Coverage → Evidence (file paths + reproducibility command) → "what's still missing" / "deployer responsibility" residual line. Gaps are stated explicitly.

See also [`docs/mappings/README.md`](docs/mappings/README.md) for reading conventions and cadence.

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- **Got a question, integration scenario, or roadmap idea?** Open a [Discussion](https://github.com/halvrenofviryel/phionyx-research/discussions). Q&A, Ideas, and Show-and-tell categories are open; the v0.4.0 roadmap conversation lives in [Ideas #77](https://github.com/halvrenofviryel/phionyx-research/discussions/77).
- **Want to ship code?** Pick a [Good First Issue](https://github.com/halvrenofviryel/phionyx-research/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22). Each one has acceptance criteria, a layer label, and a determinism contract clause — small, scoped, reviewable.
- **Found a bug or hit an unexpected behaviour?** Open an [Issue](https://github.com/halvrenofviryel/phionyx-research/issues/new/choose).

---

## License

**AGPL-3.0** — See [LICENSE](LICENSE) for details.

A commercial license is available for use cases where AGPL-3.0 copyleft is not suitable. Patent rights retained by Phionyx Research. See [PATENT_NOTICE.md](PATENT_NOTICE.md).

---

## Documentation & Research

- **Research website:** [phionyx.ai](https://phionyx.ai)
- **Posts (Deterministic AI Engineering series):** [phionyx.ai/research/posts](https://phionyx.ai/research/posts)
- **Substack (read direct):** [phionyxresearch.substack.com](https://phionyxresearch.substack.com)
- **Companion repo (Evaluation Standard):** [phionyx-evaluation-standard](https://github.com/halvrenofviryel/phionyx-evaluation-standard) — JSON Schema for governance evidence rows + worked examples
- **MCP outward layer:** [phionyx-mcp-server](https://github.com/halvrenofviryel/phionyx-mcp-server) — MCP trust boundary governance (descriptor hash, signed RGE v0.2 envelope, audit chain)
- **MCP inward layer:** [phionyx-pipeline-mcp](https://github.com/halvrenofviryel/phionyx-pipeline-mcp) — self-governance gate over the agent's own "fixed / tested / changed" claims
- **Inspect AI bridge:** [phionyx-eval-inspect](https://github.com/halvrenofviryel/phionyx-eval-inspect) — RGE envelope chain → Inspect `.eval` log; viewable with `inspect view`

### Latest essays in the series

- [Post 4 — The Phionyx Architecture: Treating LLMs as Sensors, Not Oracles](https://phionyxresearch.substack.com/p/the-phionyx-architecture-treating) (2026-05-09)
- [Post 3 — The LLM Is Not the Product](https://phionyxresearch.substack.com) (2026-05-01)
- [Post 2 — Inside the 46-Block Deterministic AI Pipeline](https://phionyxresearch.substack.com/p/inside-the-46-block-deterministic) (2026-04-28)
- [Post 1 — Why Every AI Runtime Needs a Kill Switch](https://phionyxresearch.substack.com/p/why-every-ai-runtime-needs-a-kill) (2026-04-24)

---

## Links

- **Website:** [phionyx.ai](https://phionyx.ai)
- **Author / ORCID:** [0009-0002-3718-4010](https://orcid.org/0009-0002-3718-4010)
- **arXiv Paper 1 (Architecture):** Submission in moderation (cs.AI primary, cs.SE secondary) — ID will be added when announced
- **arXiv Paper 2 (Evidence Protocol):** Paused, gated on Paper 1 ID + repo alignment

---

## Citation

If you use Phionyx Core in academic work, please cite both the software and the architecture paper.

**Software (this repository):**

```bibtex
@software{abak2026phionyxcore,
  author    = {Abak, Ali Toygar},
  title     = {Phionyx Core SDK},
  year      = {2026},
  publisher = {Phionyx Research},
  version   = {0.3.0},
  doi       = {10.5281/zenodo.20027534},
  url       = {https://doi.org/10.5281/zenodo.20027534}
}
```

The DOI above is the **concept DOI** — it always resolves to the latest archived version. To pin a specific release, use the version DOI in [`CITATION.cff`](CITATION.cff): v0.3.0 is `10.5281/zenodo.20027535`; v0.4.0 is `10.5281/zenodo.20297990`.

**Architecture paper (companion):**

```bibtex
@techreport{abak2026phionyx,
  author      = {Abak, Ali Toygar},
  title       = {Phionyx: A Deterministic AI Runtime Architecture with Structured State Management and Pre-Response Governance},
  institution = {Phionyx Research},
  year        = {2026},
  url         = {https://github.com/halvrenofviryel/phionyx-research}
}
```

A machine-readable [`CITATION.cff`](CITATION.cff) is provided for GitHub's “Cite this repository” widget; both the concept and version DOIs are registered there.
