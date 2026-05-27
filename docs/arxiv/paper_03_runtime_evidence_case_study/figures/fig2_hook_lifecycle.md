# Figure 2 — Claude Code lifecycle with 15 hook attachment points + subagent layer

```mermaid
flowchart TB
    SS["SessionStart"] --> UPS["UserPromptSubmit"]
    UPS --> PTU["PreToolUse"]
    PTU -->|matcher: Bash<br/>git commit/push| H1["check_mcp_gate.py<br/><b>BLOCKING</b>"]
    PTU -->|matcher: Bash<br/>gh/npm/docker/kubectl/...| H2["check_bash_external_effect.py<br/><b>BLOCKING</b>"]
    PTU -->|matcher: Edit/Write/<br/>MultiEdit/NotebookEdit| H3["check_edit_gate.py<br/><b>BLOCKING</b>"]
    PTU -->|matcher: Agent| H4["check_agent_spawn.py<br/><b>BLOCKING</b>"]
    PTU -->|matcher: mcp__.*| H5["check_mcp_tool_call.py<br/>observability"]
    H1 --> TOOL["tool execution"]
    H2 --> TOOL
    H3 --> TOOL
    H4 --> TOOL
    H5 --> TOOL
    TOOL --> PoTU["PostToolUse"]
    PoTU -->|matcher: Bash<br/>git commit| H6["auto_attest_commit.py<br/>observability"]
    PoTU -->|matcher: WebFetch/<br/>WebSearch| H7["log_external_ingress.py<br/>observability"]
    PoTU -->|matcher: Edit/Write/<br/>MultiEdit/NotebookEdit<br/><b>v0.7.2 P2</b>| H13["post_edit_language_check.py<br/>py_compile + ruff /<br/>tsc / json / yaml /<br/>memory_schema<br/>observability"]
    H6 --> STOP["Stop"]
    H7 --> STOP
    H13 --> STOP
    STOP --> H8["check_question_grounding.py<br/><b>BLOCKING</b><br/>(always-on)"]
    STOP -->|<b>v0.7.2 P4</b>| H14["run_targeted_tests.py<br/>diff → pytest routes<br/>observability"]
    H8 --> SUBSTOP["SubagentStop"]
    H14 --> SUBSTOP
    SUBSTOP --> H9["attest_subagent_stop.py<br/>observability"]
    H9 --> PRE["PreCompact"]
    PRE --> H10["pre_compact_checkpoint.py<br/>observability"]
    H10 -.->|on UserPromptSubmit| UPS_HOOK
    UPS -.-> UPS_HOOK["log_user_prompt.py<br/>observability"]
    SS -.-> SS_HOOK["session_start_attest.py<br/>observability"]
    SS -.->|<b>v0.7.1 F-MS1</b>| MEM_HOOK["check_memory_schema.py<br/>frontmatter validation<br/>observability"]

    SUBAGENT["diff-reviewer subagent<br/>fresh context, Read-only<br/><b>v0.7.2 P1</b>"]
    PTU -.->|invoked manually:<br/>'Use the diff-reviewer<br/>subagent to check this commit'| SUBAGENT
    SUBAGENT -.->|findings as tool result| ASST[("Implementing<br/>session")]

    classDef blocking fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,font-weight:bold
    classDef observe fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef event fill:#f3f4f6,stroke:#4b5563,color:#1f2937
    classDef exec fill:#f5d0fe,stroke:#a21caf,color:#581c87
    classDef subagent fill:#fef3c7,stroke:#d97706,color:#78350f,font-weight:bold
    class H1,H2,H3,H4,H8 blocking
    class H5,H6,H7,H9,H10,H13,H14,UPS_HOOK,SS_HOOK,MEM_HOOK observe
    class SS,UPS,PTU,PoTU,STOP,SUBSTOP,PRE event
    class TOOL exec
    class SUBAGENT,ASST subagent
```

**Caption.** Fifteen hooks are wired to seven Claude Code lifecycle events. Five hooks are **blocking** (red): they refuse the tool call when a recent gate invocation is missing, with strict mode (`PHIONYX_MCP_GATE_STRICT=1`) escalating warnings to hard blocks. Ten hooks are **observability** (blue): they write `auto_attest` entries that contribute to activity visibility but are **excluded from coverage math** by construction (see §5.3). The `check_question_grounding.py` Stop hook is always-on (no env-var disable) and blocks responses that reference unread artefacts. The three v0.7.2 additions (rows 13–14 in Table 1, plus the row 7 memory-schema check that shipped in v0.7.1) close the *feedback* gap: per-edit language tools, per-Stop targeted tests, and per-session memory-schema validation. The **adversarial diff-reviewer subagent** (orange, v0.7.2 P1) sits above the hook layer — invoked manually, runs in a fresh context, returns findings as a tool result. Together, the blocking class binds gate invocation deterministically while the subagent layer adds semantic review that no syntactic hook can perform.
