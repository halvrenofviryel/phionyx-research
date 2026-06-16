# Off-agent control plane (M1 #1-3) — bubblewrap sandbox

The agent (Claude Code) **must not be able to rewrite what governs it** — the
hooks, `.claude/settings.json`, the MCP server, the signer code, or `leak_scan.py`
— and **must not hold the signing key**. This directory makes that real on this
host.

## Why a sandbox, not filesystem permissions

The provisioning script (`scripts/active/provision_offagent_control.sh`) tries to
make the control plane read-only to a separate agent user via `chown`/`chmod`.
That **cannot work on every filesystem**: on an **NTFS** mount (`ntfs-3g`), for
example, every file is forced to `root:root 777` and `chown`/`chmod` are silently
ignored — so permission-based isolation does not hold there.

A **read-only bind mount** is enforced by the kernel VFS *before* the request
reaches the filesystem, so it holds even over NTFS. Proven: a `:ro` mount of
`.claude/` rejects writes with `EROFS` even though NTFS says `777`. This sandbox
uses that mechanism via `bwrap`.

## What it enforces

| Surface | In the sandbox |
|---|---|
| `.claude/`, `tools/claude_code_mcp`, `tools/phionyx_mcp_server`, `tools/offagent`, `.git/hooks`, `leak_scan.py` | **read-only** (run/read yes, rewrite no) |
| `~/.phionyx/keys` (private key) | **masked** (tmpfs — invisible) |
| `~/.phionyx/pub` (public key), `~/.phionyx/state` (signed state) | read-only |
| repo body, `~/.claude` (OAuth/session) | read-write (agent works normally) |
| `PHIONYX_SIGNED_GATE`, `PHIONYX_OFFAGENT` | `=1` (fail-closed gate armed) |

The private key stays with **you** (the host signer). The agent holds only the
public key — it can *verify* signed state but cannot *forge* it.

## One-time enablement (needs sudo — Ubuntu 24.04)

`bwrap` needs unprivileged user namespaces, which Ubuntu 24.04 restricts
(`kernel.apparmor_restrict_unprivileged_userns=1`). Install the **scoped** profile
that grants this to `bwrap` only (the global hardening stays in force otherwise):

```bash
sudo cp tools/offagent/apparmor-bwrap /etc/apparmor.d/bwrap
sudo apparmor_parser -r /etc/apparmor.d/bwrap
```

## Setup + run

```bash
# 1. one-time: create pub/ + state/ from the existing keypair
tools/offagent/setup.sh

# 2. terminal A — run the host signer (holds the private key, OUTSIDE the sandbox)
tools/offagent/signer-loop.sh

# 3. terminal B — prove the boundary, then launch the agent sandboxed
tools/offagent/run-agent.sh bash tools/offagent/verify-boundary.sh   # all PASS
tools/offagent/run-agent.sh                                          # launches claude
```

## M1 #5 — making the sandbox the default launch path

The boundary above only holds when the agent is launched via `run-agent.sh`. A
**direct `claude` launch** bypasses everything (on NTFS the control plane is `777`,
the key is readable, and `PHIONYX_SIGNED_GATE` is agent-writable). M1 #5 closes the
*accidental / cooperative* version of that hole two ways:

1. **Env-independent, default-on enforcement.** `check_signed_control_state.py` now
   arms on **filesystem ground truth** (`sandbox_probe.sandbox_intact()` — control
   plane actually read-only **and** the private key actually masked), not on the
   agent-writable `PHIONYX_SIGNED_GATE`. A commit/push from a session that is **not
   provably sandboxed is DENIED by default**. Off-agent dev escape: create
   `~/.phionyx/unsandboxed_dev_ok` (one-line reason) — logged. The escape **persists
   until you manually remove it** (not consumed on use, so a commit+push pair both
   pass); delete it when done. The sentinel path is **hardcoded** (no env override) so
   no agent-writable env can relocate or fake it. SessionStart attests `sandbox_intact`
   and prints a loud stderr warning when not.

2. **A `claude` wrapper that auto-sandboxes repo work.** Installed AS
   `~/.local/bin/claude` (replacing the version symlink):

   ```bash
   readlink -f ~/.local/bin/claude > ~/.phionyx/m1_5_staging/claude_symlink_backup.txt  # backup target
   cp ~/.phionyx/m1_5_staging/claude_wrapper.sh ~/.local/bin/claude && chmod +x ~/.local/bin/claude
   ```

   Inside the repo it re-execs through `run-agent.sh` (→ `PHIONYX_OFFAGENT=1`); any
   other cwd passes straight through to the real binary. It resolves the real binary
   dynamically (newest `~/.local/share/claude/versions/*`) so it survives version
   bumps.

   > **FRAGILITY — re-install after self-update.** A Claude Code self-update rewrites
   > `~/.local/bin/claude` back to a plain symlink, silently dropping the wrapper.
   > Re-run the `cp` above after any update. A major install-path change needs a
   > manual re-point of `REAL` in the wrapper.

**Live-verified 2026-06-14** (from the unsandboxed apply session): probe reports
`sandbox_intact = False` unsandboxed; a `git commit` is BLOCKED by default with no
env and no sentinel; the dev sentinel re-allows it. (Could not be written from the
prior sandboxed session — EROFS on the control plane.)

**Honest scope of #5:** this closes the accidental/cooperative direct-launch path and
raises the cost of the adversarial one (the escape sentinel + the hook code are still
agent-writable when unsandboxed; tampering is itself gated and leaves evidence). Full
adversarial closure (the agent cannot escape even by editing the hook or forging the
sentinel) needs **off-agent custody / separate OS user — Phase 3 / the deeper
milestone**, partly blocked here by the same NTFS `chmod` no-op.

## M1 #6 — signed human override (the strong escape)

The plain sentinels above (`unsandboxed_dev_ok`, `control_plane_edit_approved`) are
cooperative-dev fallbacks — agent-writable, so not tamper-proof. The **strong** override
is an Ed25519-signed, scoped, expiring token the founder mints **off-agent** (the private
key is masked inside the sandbox, so signing only works outside it):

```bash
# allow an unsandboxed commit/push for 1h:
python3 tools/claude_code_mcp/control_override.py --sign --scope unsandboxed_commit --reason "release cut" --ttl 3600
# allow a control-plane edit:
python3 tools/claude_code_mcp/control_override.py --sign --scope control_plane_edit --reason "hook fix" --ttl 1800
python3 tools/claude_code_mcp/control_override.py --show      # inspect / time-left
python3 tools/claude_code_mcp/control_override.py --revoke    # delete the token
```

The gates verify it with the PUBLIC key (an agent holding only the public key cannot
forge it), enforce the **scope** (a commit token cannot unlock an edit, and vice-versa)
and the **expiry**, and record a `signed_override_used` attestation. Token path:
`~/.phionyx/state/control_override.signed.json` (hardcoded; ro-bound into the sandbox).
The verify key is **pinned** to `~/.phionyx/pub/control_ed25519.pub` (hardcoded, not the
agent-writable `PHIONYX_KEY_DIR`) so env relocation cannot route verification to a forged
key. Honest residual: on this dev box the private key is still agent-readable AND the
agent could overwrite `~/.phionyx/pub` (*signed, custody-pending*) — it becomes
unforgeable once both the key and the trusted-pub dir are off-agent (in the sandbox the
pub dir is already ro-bound).

## Scope — what this does and does NOT do

- ✅ The agent **cannot rewrite** the hooks/config/signer/leak-scan (kernel-enforced).
- ✅ The agent **cannot read** the private key; only the host signer can sign.
- ⚠️ The signed state's *content* is still derived from agent-writable telemetry
  (`data/mcp_telemetry/`). Making the signed verdict independent of agent-writable
  inputs is a **separate, deeper milestone** — not delivered here.
- ❌ Not "containment of a superintelligence." This is a write-boundary on specific
  files plus key custody. Keep the framing modest.
