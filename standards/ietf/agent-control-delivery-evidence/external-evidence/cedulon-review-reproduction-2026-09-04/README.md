# Author-side reproduction of the Cedulon focused-review measurements

**Date of reproduction:** 4 September 2026
**Performed by:** the author of `draft-abak-agent-control-delivery-evidence`

## What this is, and what it is not

This directory records an **author-side independent reproduction** of
measurements that **Emek Can Dogru** reported during focused review of the `-01`
candidate. The author reran the reviewer's own pinned case driver against the
**published** Cedulon npm package sets and preserved the raw output.

It **is**:

- an independent *reproduction* of reviewer-reported measurements;
- run against published packages from the public npm registry;
- run with the reviewer's pinned driver, byte-for-byte unmodified;
- run from two separate clean directories created outside every git clone.

It is **not**:

- an independent *implementation* of Cedulon;
- an implementation of `draft-abak-agent-control-delivery-evidence`;
- a repin, replacement, correction, or rewrite of the historical
  1 September 2026 Cedulon population probe;
- a conformance result for this document;
- an interoperability result between two implementations;
- an IETF, working-group, or SCITT endorsement of anything.

Cedulon remains **adjacent-domain evaluation evidence**. Nothing here describes
Cedulon as an implementation of this document, and nothing here is evidence that
this document has an implementation.

## Source driver — referenced, not vendored

The driver is **not** copied into this repository. Only its identity is recorded.

| Field | Value |
|---|---|
| Repository | `dogrucanemek-alt/cedulon` |
| Commit | `52cf577` |
| Path | `interop/abak-00/cases-0.12.0.mjs` |
| Raw URL | <https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/52cf577/interop/abak-00/cases-0.12.0.mjs> |
| Observed SHA-256 | `f7f1218abd1535f104b0010b9127c565b3afab0e72242583ebc459000937bc8e` |
| Lines | 135 |
| Bytes | 6153 |
| CR bytes | 0 (LF only) |
| `file` | JavaScript source, ASCII text |

The line count, byte count, and line-ending properties match the values the
reviewer stated for this file exactly.

**On the driver digest.** No copy of the review message stating a SHA-256 for
this driver is held in this work area, so **the digest above is the value this
work area observed**, not a digest checked against a reviewer-stated value. It is
recorded as an observation and anchored on the pinned commit, path, and size
metadata, which do match. This is a gap in the local record, and it is stated
rather than papered over: no expected digest was invented.

The same driver bytes were used for **both** runs. No modified "0.8.0 driver" was
created — the driver's own header says to substitute the package version and rerun
the same file, which is what was done.

## Packages

Published packages from `https://registry.npmjs.org/`. Per-package license,
`dist.integrity`, `dist.shasum`, and tarball URL are in `REGISTRY_METADATA.json`
for all 14 package-versions. Every one declares `Apache-2.0`.

| Run | Direct installs | Full resolved `@cedulon/*` graph |
|---|---|---|
| 0.12.0 | `audit`, `receipts`, `checkpoint`, `x402-adapter` @ `0.12.0` | `audit`, `checkpoint`, `core`, `cose`, `manifest`, `receipts`, `x402-adapter` — **all `0.12.0`** |
| 0.8.0 | `audit`, `receipts`, `checkpoint`, `x402-adapter` @ `0.8.0` | `audit`, `checkpoint`, `core`, `cose`, `manifest`, `receipts`, `x402-adapter` — **all `0.8.0`** |

Both graphs are homogeneous at the requested version and contain no third-party
dependencies, so neither run is a mixed-version graph. No npm `overrides` were
added and no version was forced.

**Lifecycle scripts.** Before installing, `preinstall`, `install`, and
`postinstall` were checked for all 14 package-versions. **None publishes any of
them** — each publishes only a `build` script, which npm does not run at install
time. `--ignore-scripts` was therefore **not** used, so the reviewer's invocation
contract was preserved rather than altered.

## Environment

| Field | Value |
|---|---|
| UTC | 2026-09-04T03:19:23Z |
| OS | Linux 6.11.0-29-generic (Ubuntu 24.04), `x86_64` |
| Node | `v20.19.6` |
| npm | `10.8.2` |
| Registry | `https://registry.npmjs.org/` |

Only non-secret environment metadata is recorded. No tokens, credentials, npm or
GitHub auth, or home-directory contents appear in this directory.

## Runs

| Run | npm install exit | node exit | stderr | stdout SHA-256 | `package-lock.json` SHA-256 |
|---|---|---|---|---|---|
| 0.12.0 | 0 | **0** | empty (0 bytes) | `d01ac0e023a3c8f6f376a4235a9adb6b3e2ef4d64dc3bd9dfc27921fbb5bd25e` | `2e5abc4b453475893cb5ed6c6160cd50d6e5fcf87e059cf06adc5d24eb90a239` |
| 0.8.0 | 0 | **0** | empty (0 bytes) | `201d0a527234be8e702debd005e437ae08d4c28db842d64462f7a29b4157a8a7` | `dbe8f166bea9dba0c8046c9e7d29108299d46bc3849fd323e9b43d427862b158` |

Each run used its own freshly created `mktemp -d` directory outside every git
clone, so the imports resolve to the published packages rather than to any
working tree. Node's exit status was captured directly, not through a pipe.

## Result

**Reproduction: PASS.** See `RESULTS.md` for the case-by-case matrix and the
exact claims tested.

## The historical probe is unchanged

The 1 September 2026 Cedulon population probe — commit `0a3fa04`, SHA-256
`031f84fda2054b1427a510baa45f880d379ea60dced408a4a74028da12b1fceb`, recorded in
`../CEDULON_POPULATION_PROBE.md` — was **not** edited, repinned, replaced, or
rewritten by this reproduction. It remains historical pinned evidence of what was
measured against the package versions it was run against.

This reproduction is a **separate, later evidence event** with its own driver,
its own packages, and its own date. The two are not merged, and the newer result
does not retroactively restate the older one.

## Files

| File | Contents |
|---|---|
| `README.md` | this file |
| `RESULTS.md` | case-by-case matrix and claim-by-claim outcome |
| `ENVIRONMENT.json` | machine-readable environment, driver identity, run metadata |
| `REGISTRY_METADATA.json` | npm registry metadata for all 14 package-versions |
| `npm-ls-0.8.0.json`, `npm-ls-0.12.0.json` | full resolved dependency graphs |
| `run-0.8.0.stdout.txt`, `run-0.12.0.stdout.txt` | raw captured stdout |
| `run-0.8.0.stderr.txt`, `run-0.12.0.stderr.txt` | raw captured stderr (both empty) |
| `SHA256SUMS.txt` | digests of every file in this directory |
