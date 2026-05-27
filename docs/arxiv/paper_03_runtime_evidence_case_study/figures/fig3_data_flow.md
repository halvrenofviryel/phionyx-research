# Figure 3 — Data flow from prompt to coverage metric

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Asst as Assistant<br/>(Claude)
    participant Hook as Pre-tool hook<br/>(check_edit_gate)
    participant Pipe as Pipeline MCP<br/>(response_gate)
    participant Tool as Tool runtime<br/>(Edit, Bash, ...)
    participant Tel as data/mcp_telemetry/<br/>session_&lt;trace&gt;.json
    participant Git as git log
    participant Audit as runtime_evidence_<br/>self_audit.py
    participant Out as docs/strategic/<br/>self_audit_&lt;DATE&gt;.md

    User->>Asst: prompt (request a change)
    Asst->>Pipe: phionyx_response_gate(action=claim_fixed, ...)
    Pipe-->>Tel: write directive entry (pass | reject | regenerate)
    Pipe-->>Asst: directive
    Asst->>Hook: PreToolUse: Edit("paper.md", ...)
    Hook->>Tel: read recent gate calls
    alt no gate call in window
        Hook-->>Asst: BLOCK (strict mode)
    else gate call within 30 min
        Hook-->>Tool: allow
        Tool->>User: applied edit
        Tool->>Tel: PostToolUse hook writes auto_attest entry
    end
    User->>Asst: "commit"
    Asst->>Hook: PreToolUse: Bash("git commit")
    Hook->>Tel: read recent gate calls
    alt no recent gate
        Hook-->>Asst: BLOCK
    else recent gate
        Hook-->>Tool: allow
        Tool->>Git: commit SHA
        Tool->>Tel: PostToolUse writes commit_attestation
    end

    Note over Tel,Git: ... time passes; agent does more commits ...

    User->>Audit: python3 scripts/active/runtime_evidence_self_audit.py --days 30
    Audit->>Tel: read all session_*.json
    Audit->>Git: read commits in window
    Audit->>Audit: filter gate-class directives<br/>(exclude auto_attest)
    Audit->>Out: write markdown report
    Out-->>User: coverage = gate_calls / (2 × commits)
```

**Caption.** Each commit cycle traverses two blocking gates: the pre-Edit gate enforces that a recent `phionyx_response_gate` call exists before any non-trivial file mutation, and the pre-commit Bash gate enforces the same before the commit. Successful commits emit a PostToolUse `commit_attestation`. Observability hooks (PostToolUse on commits and WebFetch/WebSearch, plus SessionStart/UserPromptSubmit/PreCompact/SubagentStop/mcp__.*) write `auto_attest` entries. The self-audit script reads the resulting telemetry plus `git log`, filters the gate-class directives (excluding `auto_attest`), and produces a deterministic coverage report at `docs/strategic/runtime_evidence_self_audit_<DATE>.md`.
