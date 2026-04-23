# Phionyx Core SDK - Licensing Strategy

**Dual-License Model: AGPL-3.0 + Commercial License**

---

## Executive Summary

Phionyx Core SDK follows a **dual-license** model:

- **Open Source**: AGPL-3.0 (copyleft — derivative works and network use must also be AGPL-3.0)
- **Commercial License**: Available for users who cannot comply with AGPL-3.0 copyleft obligations
- **Patent Protection**: No patent grant under AGPL-3.0 — all patent rights retained by Phionyx Research

---

## 1. Why AGPL-3.0?

### Benefits

- **Copyleft protection**: Anyone modifying or using the SDK in a network service must release their source code
- **No patent grant**: Patent rights remain fully with Phionyx Research, enabling patent licensing revenue
- **Dual-license revenue**: Organizations wanting proprietary use must purchase a commercial license
- **Academic-friendly**: Academic and research use is unrestricted (copyleft is not a burden for published research)
- **Proven model**: Used by MongoDB, Grafana, Minio, and other successful open-source companies

### Compared to Apache 2.0

| | Apache 2.0 | AGPL-3.0 |
|---|---|---|
| Patent grant | Automatic for SDK users | None — retained |
| Copyleft | No | Yes — source disclosure required |
| Commercial use without license | Unrestricted | Must comply with copyleft |
| Revenue potential | Lower | Higher (dual-license + patent) |
| Academic adoption | High | High (copyleft not a burden) |

---

## 2. Dual-License Boundary

### AGPL-3.0 (Open Source)

Available to everyone:

- Core pipeline orchestration
- EchoState and structured state management
- Risk scoring interface
- Policy hooks (interface)
- SDK API contracts
- Evaluation hooks (standard compliance)

### Commercial License (Paid)

For organizations that cannot or prefer not to comply with AGPL-3.0:

- Same Core SDK code, different license terms
- No source-disclosure obligation
- May include patent license
- Custom support and SLA options

### Proprietary Products (Separate)

Not part of the Core SDK, always require commercial license:

- Governance Node (decision authority, 4-gate structure)
- Evidence Store (audit logs, replay database)
- Certification Engine (compliance verification)

---

## 3. Patent + License Alignment

### Structure

1. **Core SDK LICENSE** (AGPL-3.0)
   - Open source with copyleft
   - No patent grant

2. **PATENT_NOTICE.md** (separate file)
   - Lists related patents (4 families, 66 claims)
   - Clarifies patent rights retention
   - Defines commercial licensing path

### Revenue Streams

| Stream | Source |
|---|---|
| Patent licensing | Independent implementations of patented methods |
| Commercial SDK license | Organizations avoiding AGPL-3.0 copyleft |
| Proprietary products | Governance Node, Evidence Store, Certification |
| Book sales | Amazon KDP (passive income) |

---

## 4. Competitive Protection

### If Competitor Forks Core SDK

**Under AGPL-3.0:**
1. They must release their modifications under AGPL-3.0
2. If they use it in a network service, they must release all source code
3. No patent rights transfer — they may need a patent license
4. They cannot offer a proprietary version without a commercial license from us

**Result**: Much stronger protection than Apache 2.0.

---

## 5. Files

- `LICENSE`: AGPL-3.0 license text
- `PATENT_NOTICE.md`: Patent information and commercial licensing
- `LICENSE_STRATEGY.md`: This document (strategic overview)

---

## 6. Contact

- **Open Source License**: See LICENSE file (AGPL-3.0)
- **Patent Information**: See PATENT_NOTICE.md
- **Commercial Licensing**: founder@phionyx.ai

---

**Last Updated**: 2026-04-23
