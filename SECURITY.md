# Security Policy

## Reporting a vulnerability

If you discover a security issue in `phionyx-core` or any code in this
repository, please **report it privately** rather than opening a public
issue.

Use one of:

- GitHub's [private vulnerability reporting](https://github.com/halvrenofviryel/phionyx-research/security/advisories/new)
  for this repository (recommended — it gives the maintainer a direct,
  encrypted channel and an audit trail).
- Email: `founder@phionyx.ai`. Use the subject line `Security:
  phionyx-core`.

We aim to acknowledge new reports within **3 business days** and to
ship a fix or a disclosure timeline within **30 days** of
acknowledgement, depending on severity. There is no bug bounty
programme; we treat coordinated disclosure as the norm and credit
reporters in the release notes when they want to be named.

## Scope

In scope:

- Runtime safety bypasses — anything that lets an external input
  cause `phionyx_core.governance.kill_switch.KillSwitch` to remain
  armed when the documented triggers fire.
- Audit-record forgery — a path that produces an `AuditRecord` whose
  `compute_hash()` value matches a different chain than the one it
  was actually written into.
- Determinism violations — an input that causes any block declared as
  `determinism = "strict"` to produce different outputs on identical
  `BlockContext`.
- Capability escape — an input that causes a block to invoke an
  effect that its `RunCapabilities` declared it could not.
- Pipeline contract violations — silent skipping of a canonical block
  without a recorded `policy_bypass` audit entry.
- Secret exfiltration through the standard install path
  (`pip install phionyx-core`) — environment variables, file reads, or
  network calls outside what the documented adapters perform.

Out of scope:

- Issues in optional `[graph]`, `[postgres]`, `[supabase]` adapters
  that originate in the underlying upstream library — please report
  those upstream and link the upstream issue here.
- Issues that depend on running the package with manually disarmed
  governance (e.g. `KillSwitchState.DISARMED`, custom profiles that
  set `enabled: false` on safety blocks). The disarmed state is a
  testing convenience documented as such.
- Self-DoS scenarios — e.g. constructing pathological input that
  causes the local process to exhaust memory. We will fix these on a
  best-effort basis but do not treat them as security advisories.

## Supported versions

Only the latest minor release on PyPI receives security fixes. As of
v0.2.x, that means v0.2.1 and any subsequent v0.2.x patch. v0.1.x is
not supported.

| Version line | Status        |
|--------------|---------------|
| v0.2.x       | Supported     |
| v0.1.x       | Not supported |

## Handling

When a report is accepted:

1. We confirm receipt and assign a tracking ID privately.
2. We reproduce the issue and assess severity (CVSS-like, no formal
   scoring at this size).
3. We prepare a fix on a private branch.
4. We publish a [GitHub Security Advisory](https://github.com/halvrenofviryel/phionyx-research/security/advisories)
   with the patched version and credit the reporter (if they consent).
5. We push the fix to `main` and tag a patch release; the OIDC release
   workflow handles the PyPI upload.

## Cryptographic primitives

`phionyx_core` uses Ed25519 for `AuditRecord` signatures via the
standard library `nacl` binding. We do not roll our own crypto. If you
spot a misuse — wrong key handling, weak key generation, replayed
nonces, etc. — please file a report under this policy.

## Defensive patent pledge

A separate concern, but worth noting in the same context: the
[`PATENT_PLEDGE.md`](PATENT_PLEDGE.md) at repo root commits to not
asserting our patent claims against good-faith open-source users.
Coordinated security disclosure is one of the activities the pledge
explicitly covers.
