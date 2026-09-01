# Sources

Every source consulted while building this work area. All entries were retrieved
on **2026-09-01** unless stated otherwise. Dates and revision numbers are taken
from the sources themselves (mail headers, the published draft, the IETF
Datatracker API, and the `rfc-editor.org` metadata), not from prose summaries.

Digests below are SHA-256 of the exact bytes retrieved.

---

## 1. Published Internet-Draft baseline (`-00`)

| Type | Author / project | Date | Purpose | URL | Revision | Digest (SHA-256) | Notes |
|---|---|---|---|---|---|---|---|
| I-D landing page | Ali Toygar Abak (Independent Researcher) | posted 2026-08-31; submitted 2026-08-29 | Canonical Datatracker record | <https://datatracker.ietf.org/doc/draft-abak-agent-control-delivery-evidence/> | `-00` | — | Group: "Individual Submissions". State: Active / I-D Exists. |
| I-D source (XML) | Ali Toygar Abak | document date 30 August 2026 | Authoritative source for what `-00` states and cites | <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-00.xml> | `-00` | `8ed78f9428ee9a9f0d13526fee04055fef8d16809996ac2932c7907cdfc4d3da` | Stored unmodified at `draft/published/00/`. |
| I-D rendered (TXT) | Ali Toygar Abak | 30 August 2026 | Human-readable baseline | <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-00.txt> | `-00` | `414fcae84d4b6b778068e9b9e47df56b9b56d4a523ff220599ef82c238e1e9cf` | Stored unmodified. |
| I-D rendered (HTML) | Ali Toygar Abak | 30 August 2026 | Human-readable baseline | <https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-00.html> | `-00` | `a242c3f7e2592b0d1deb262996434e2ae1f6f3400fe07cd51a921ef784012557` | Stored unmodified. |

Verified directly from the `-00` XML/TXT:

- `docName="draft-abak-agent-control-delivery-evidence-00"`;
- `category="info"` (TXT header: "Intended status: Informational");
- author `Ali Toygar Abak`, organization `Independent Researcher`;
- the abstract states the requirements are *format-independent* and that the
  document "does not define a receipt format, wire protocol, authorization
  system, policy language, transparency service, or audit regime";
- Section 4 separates issuer-side emission (4.1), receiver-side observation
  (4.2), enforcement outcome (4.3), and control-effect observation (4.4).

---

## 2. Public SCITT mailing-list thread

Subject line for all fifteen messages:
`[SCITT] (Re:) New I-D: Evidence Requirements for Agent Control Delivery and Outcome Reconciliation (draft-abak-agent-control-delivery-evidence-00)`

| Ref | Type | Author | Date (as sent) | Purpose | URL |
|---|---|---|---|---|---|
| A | Announcement | Ali Toygar Abak `<founder@phionyx.ai>` | Mon, 31 Aug 2026 21:33:49 +0300 | Announces `-00`; asks four review questions | <https://mailarchive.ietf.org/arch/msg/scitt/UWud7Jg9bN7xHntkH1WPNNn0Dhc/> |
| B | Review | Iman Schrock `<team@emiliaprotocol.ai>` (EMILIA Protocol) | Mon, 31 Aug 2026 12:05:16 -0700 | Target multiplicity; freeze race; offers a fixture | <https://mailarchive.ietf.org/arch/msg/scitt/nmX5kiPFudYFDhKIHuno-0hLD8U/> |
| C | Author response | Ali Toygar Abak | Mon, 31 Aug 2026 22:55:52 +0300 | Accepts the target-multiplicity gap; proposes instruction × required-target obligations | <https://mailarchive.ietf.org/arch/msg/scitt/kW9z4Btvou0I568hk4-5NlH17G8/> |
| D | Review | Tiago Pinto `<tiago@donttrustverify.pt>` | Mon, 31 Aug 2026 19:10:17 +0000 | Contestability composition seam (partial read, scoped to Q4) | <https://mailarchive.ietf.org/arch/msg/scitt/7kC3d2XZuGpvnBMkKwwkBm2Yy7w/> |
| E | Author response | Ali Toygar Abak | Mon, 31 Aug 2026 23:10:02 +0300 | Agrees it is a composition seam, not duplication | <https://mailarchive.ietf.org/arch/msg/scitt/xyd1v3mIPRO7GvIUBunwePrjvG8/> |
| F | Review | Emek Can Dogru `<e.dogru@conarium.dev>` (Cedulon / Conarium) | Mon, 31 Aug 2026 20:52:31 +0000 | Cedulon as opposite-direction adjacent domain; bounded-population rule found a real Cedulon scope defect; Section 6.4 second-axis question | <https://mailarchive.ietf.org/arch/msg/scitt/0DEnFwL01UQXxsO954NhgevgNGk/> |
| G | Author response | Ali Toygar Abak | Tue, 01 Sep 2026 06:31:16 +0300 | Accepts the composition framing; wants to explore separating structural result from claim qualification without freezing vocabulary | <https://mailarchive.ietf.org/arch/msg/scitt/_R-gOpqjmM0fdOWKUvCR3RVJFqw/> |
| H | Contributed fixture | Iman Schrock | Mon, 31 Aug 2026 14:19:33 -0700 | Attaches `agent-control-delivery-freeze-race.v1.json`; states SHA-256 | <https://mailarchive.ietf.org/arch/msg/scitt/YcoTPgdpSl2RNWvcsB1p3c4VpAM/> |
| I | Author response | Ali Toygar Abak | Tue, 01 Sep 2026 06:34:21 +0300 | Confirms the digest; commits to preserving fixture ID and EMILIA credit | <https://mailarchive.ietf.org/arch/msg/scitt/Ei71eBl2k0_hW32hqvqvyGzEuAM/> |
| J | Provenance clarification | Iman Schrock | Mon, 31 Aug 2026 21:05:10 -0700 | Unchanged vs adapted fixture rule; AEB pinning | <https://mailarchive.ietf.org/arch/msg/scitt/5J5i8Y6w3WkzewIzH23oMPpb9cI/> |
| K | Review | Walter Hawkins `<wdhawkins46@gmail.com>` (Corrente Labs, Inc.) | Mon, 31 Aug 2026 19:00:45 -0500 | Supports the four-boundary separation; says SCITT Signed Statements are a natural container, no new receipt format needed | <https://mailarchive.ietf.org/arch/msg/scitt/fOhLQ8vUVoS_Rznapl6OlIaHQ_E/> |
| L | Review | Walter Hawkins | Mon, 31 Aug 2026 19:03:56 -0500 | Supports aligning with the contestability draft around explicit evidence-stage separation | <https://mailarchive.ietf.org/arch/msg/scitt/y14Ek_T_6e1IpoZYQxzKIv5ZKRc/> |
| M | Review | Walter Hawkins | Mon, 31 Aug 2026 19:06:46 -0500 | Supports the closed required-target set contract and per-target sub-dispositions | <https://mailarchive.ietf.org/arch/msg/scitt/B-SiXm6sqDnDb2da8b7zRkhhZuw/> |
| N | Author response | Ali Toygar Abak | Tue, 01 Sep 2026 06:37:10 +0300 | Confirms per-target obligation as the unit; format-neutral, compose with SCITT rather than add a receipt format | <https://mailarchive.ietf.org/arch/msg/scitt/RvBLhnvOY2_RtdtISeEMwG4Ujbw/> |
| O | Review | Emek Can Dogru | Tue, 01 Sep 2026 12:58:54 +0000 | Runnable disposition mapping and population-conservation probe, pinned at a commit; three findings | <https://mailarchive.ietf.org/arch/msg/scitt/rZvUFar7Zmy2u6OD5MFwA0kFMgg/> |

### Thread-completeness check

The public SCITT archive was searched on 2026-09-01
(<https://mailarchive.ietf.org/arch/browse/scitt/?q=agent-control-delivery-evidence>).
The search returned 24 message URLs. Each was fetched and its `Subject:` header
inspected. **Fifteen** carry the exact subject above — the fifteen listed as
A–O. The other nine belong to two different threads and are recorded here only
so the completeness check is reproducible; they were not treated as review of
this draft:

- `[SCITT] First-failure list: draft-dogru-cedulon-04` — six messages, 2026-08-30
  to 2026-08-31 (Tiago Pinto, Emek Can Dogru).
- `[SCITT] Re: Closing omission from the receiver's vantage — what a record must
  carry` — three messages, 2026-08-24 to 2026-08-28 (Walter Hawkins, Henri
  Sirkkavaara, Vernon Wharff).

No additional message with the draft's subject was found dated 2026-08-31 or
2026-09-01.

---

## 3. Contributed fixture

| Type | Contributor | Date | Purpose | URL | Digest (SHA-256) | Notes |
|---|---|---|---|---|---|---|
| Conformance fixture (JSON, 6212 bytes) | Iman Schrock / EMILIA Protocol | Mon, 31 Aug 2026 14:19:33 -0700 | Freeze-race + closed required-target composition case | Attachment of message H: <https://mailarchive.ietf.org/arch/msg/scitt/YcoTPgdpSl2RNWvcsB1p3c4VpAM/2/> | `2d8faa1b64b8a73fd0bf81b21889bbf726cbfb324af099b700499627af84203a` | Retrieved mechanically; digest matches the value stated in message H exactly. Stored unmodified at `fixtures/contributed/`. `fixture_id`: `freeze-after-provider-entry-with-multiple-required-targets`. |
| Provenance rule | Iman Schrock | Mon, 31 Aug 2026 21:05:10 -0700 | Unchanged/adapted handling; AEB pinning | <https://mailarchive.ietf.org/arch/msg/scitt/5J5i8Y6w3WkzewIzH23oMPpb9cI/> | — | See `RIGHTS_AND_PROVENANCE.md` and `fixtures/README.md`. |

---

## 4. External adjacent-domain evidence (Cedulon) — referenced, not vendored

| Type | Project | Date | Purpose | URL | Commit | Digest (SHA-256) | Notes |
|---|---|---|---|---|---|---|---|
| Probe source (`.mjs`, 403 lines, 24 005 bytes, LF, no CR) | Cedulon (`dogrucanemek-alt/cedulon`) | pinned commit; reported to SCITT 2026-09-01 | Applies `-00` Section 6 rules to Cedulon's shipped reconciler | <https://github.com/dogrucanemek-alt/cedulon/blob/0a3fa04/interop/abak-00/population-probe.mjs> (raw: <https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/0a3fa04/interop/abak-00/population-probe.mjs>) | `0a3fa04` | `031f84fda2054b1427a510baa45f880d379ea60dced408a4a74028da12b1fceb` | Identity independently checked here; matches Emek's stated values exactly. **Not vendored.** |
| Probe README | Cedulon | same commit | Run instructions and what the probe reports | <https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/0a3fa04/interop/abak-00/README.md> | `0a3fa04` | `1910b4af9028f5bcdf0d0393745d9dcab5655db61ca29b65acba453167e7a285` | 3931 bytes. Not vendored. |
| Cedulon internal review log | Cedulon | same commit | Round 5 entry; contains **older** wording/counts and a **different** file name and digest from the pinned probe | <https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/0a3fa04/docs/EXTERNAL_REVIEW.md> | `0a3fa04` | `74e3c557d53dcc2e05b36dc30ee5f41b640a14f17d1a7a207d1172df7419e6d6` | 18 209 bytes. Superseded for this workstream by message O and the pinned probe — see `external-evidence/CEDULON_POPULATION_PROBE.md`. |
| Upstream licence | Cedulon | same commit | Establishes the terms the referenced probe is published under | <https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/0a3fa04/LICENSE> | `0a3fa04` | `578ddb1a35574604e675c6155ed356ad75b909bae380dcb6d3239081626b2bd8` | 10 848 bytes. **Apache License 2.0.** Corroborated by npm metadata for `@cedulon/audit@0.8.0` (`"license": "Apache-2.0"`). No `LICENSE.md` / `LICENSE.txt` / `COPYING` / `NOTICE` at that commit's root (HTTP 404). Not vendored, not relicensed here. |
| npm packages resolved during verification run | Cedulon | — | Probe dependencies | npm registry | `@cedulon/audit@0.8.0`, `@cedulon/receipts@0.8.0`, `@cedulon/checkpoint@0.8.0`, `@cedulon/x402-adapter@0.8.0`; transitively `@cedulon/core@0.8.0`, `@cedulon/cose@0.8.0`, `@cedulon/manifest@0.8.0` | — | Installed in a clean temporary directory outside every clone. |

---

## 5. Adjacent IETF work (Datatracker metadata, retrieved 2026-09-01)

All six documents below are associated with the Datatracker group **"Individual
Submissions"** and are in document state *Active / I-D Exists*. None of them is
a working-group document.

| Document | Title | Current revision | Current revision submitted | Referenced elsewhere as | URL |
|---|---|---|---|---|---|
| `draft-schrock-action-evidence-boundary` | The Action Evidence Boundary for Consequential Agent Effects | **-05** | 2026-08-31 | `-04` in `-00` §17 and in the contributed fixture's `related_work`; message J confirms AEB "is now at -05" and that the fixture stays pinned to `-04` | <https://datatracker.ietf.org/doc/draft-schrock-action-evidence-boundary/> |
| `draft-schrock-ep-revocation-statement` | Portable Revocation Statements for Action-Bound Authorization Artifacts | **-01** | 2026-07-28 | `-01` in message B and in the fixture's `related_work` | <https://datatracker.ietf.org/doc/draft-schrock-ep-revocation-statement/> |
| `draft-schrock-ep-outcome-binding` | Outcome Binding for Authorized Actions and Independently Observed Effects | **-00** | 2026-07-28 | `-00` in message B and in the fixture's `related_work` | <https://datatracker.ietf.org/doc/draft-schrock-ep-outcome-binding/> |
| `draft-pinto-agent-authz-contestability` | Contestability Bindings for Authorized Agent Actions | **-00** | 2026-08-29 | `-00` in messages D and C | <https://datatracker.ietf.org/doc/draft-pinto-agent-authz-contestability/> |
| `draft-dogru-cedulon` | Cedulon: An Audit Layer for Agent-to-Agent Commerce | **-06** | 2026-08-31 | `-06` as posted per message F; message F also describes an unposted working `-07` | <https://datatracker.ietf.org/doc/draft-dogru-cedulon/> |
| `draft-abak-agent-control-delivery-evidence` | Evidence Requirements for Agent Control Delivery and Outcome Reconciliation | **-00** | 2026-08-29 | this work area's subject | <https://datatracker.ietf.org/doc/draft-abak-agent-control-delivery-evidence/> |

Distinguish, throughout this directory:

- the **revision an external fixture or review explicitly references** (e.g. the
  contributed fixture names AEB `-04`); from
- the **currently published revision** (AEB `-05`).

None of these drafts is copied into this repository.

---

## 6. RFC metadata checked against reviewer prose

Message K states "Existing SCITT Signed Statements (RFC 9942)". That number was
checked against `rfc-editor.org` rather than imported:

| RFC | Title (per rfc-editor.org) | Date | Status |
|---|---|---|---|
| RFC 9942 | CBOR Object Signing and Encryption (COSE) Receipts | June 2026 | Proposed Standard |
| RFC 9943 | An Architecture for Trustworthy and Transparent Digital Supply Chains | June 2026 | Proposed Standard |

The published `-00` cites **RFC 9943** in Section 8.2 and in Section 17, with
the text "[RFC9943] defines signed statements and receipts for registration in a
transparency service." RFC 9942 is a different document (COSE Receipts). The
reviewer's RFC number therefore does not match the citation in `-00`, and no
normative or related-work change has been made on the strength of the reviewer's
number. See `reviews/REVIEW_LEDGER.md` item **W-1**.
