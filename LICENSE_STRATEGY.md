# Phionyx Core SDK – Licensing Strategy

**Dual-License Model: AGPL-3.0 + Commercial License**

## Executive Summary

Phionyx Core SDK is released under a dual-license model:

- **Open Source License:** AGPL-3.0
- **Commercial License:** Available for organizations that cannot or do not wish to comply with AGPL-3.0 obligations
- **Patent Position:** The AGPL-3.0 license includes the patent-related permissions required by the license itself for the covered contributor version. Any separate commercial licensing, trademark use, certification, hosted deployment terms, or rights outside the AGPL scope are managed separately by Phionyx Research.

This means:

- researchers and open-source users may use, study, modify, and deploy the SDK under AGPL-3.0 terms;
- organizations seeking different redistribution, embedding, deployment, warranty, support, or licensing terms may request a separate commercial license;
- the public open-source release does not by itself grant use of Phionyx trademarks, certification marks, or any separate commercial service rights.

---

## 1. Why AGPL-3.0?

Phionyx Core SDK uses AGPL-3.0 because the project is intended to remain open, inspectable, and improvement-friendly, while preventing closed network deployment of modified versions without source disclosure.

### Benefits

- **Copyleft protection:** modified versions used over a network must also make source code available under AGPL-3.0 terms.
- **Transparency:** downstream users can inspect and audit the implementation.
- **Research friendliness:** academic and experimental use remains open and reproducible.
- **Commercial flexibility:** organizations needing alternative terms can obtain a separate commercial license.

---

## 2. Why offer a commercial license?

Some users cannot adopt AGPL-3.0 in production because of internal policy, redistribution models, proprietary integration constraints, or compliance requirements.

A separate commercial license may provide, depending on the agreement:

- use without AGPL copyleft obligations;
- proprietary embedding or redistribution rights;
- negotiated support, warranty, or indemnity terms;
- commercial deployment permissions under separate contractual conditions.

This is the basis of the dual-license approach.

---

## 3. Patent position

Phionyx Research retains ownership of its intellectual property, including copyrights, branding, and any patent rights not otherwise granted by the applicable open-source license.

Important clarification:

- the open-source release is made under **AGPL-3.0**;
- any patent-related permissions that arise under AGPL-3.0 apply within that license framework;
- **commercial rights outside AGPL-3.0**, including separately negotiated patent, deployment, support, branding, certification, or enterprise-use rights, are handled only through a separate written agreement.

### In plain language

Using the SDK under AGPL-3.0 does **not** make a user a commercial partner, certified implementer, or trademark licensee of Phionyx Research.

---

## 4. Compared to permissive licensing

| Topic | Apache 2.0 style approach | AGPL-3.0 approach used by Phionyx |
|---|---|---|
| Copyleft | No | Yes |
| Network source disclosure | No | Yes |
| Proprietary internal/service use without copyleft obligations | Easier | Requires AGPL compliance or separate commercial license |
| Commercial dual-license leverage | Lower | Higher |
| Downstream transparency | Lower | Higher |

Phionyx intentionally uses AGPL-3.0 because the project is designed as an auditable runtime layer, where transparency and reciprocal openness are strategically important.

---

## 5. What is open-source, and what is separate?

### Covered by the public AGPL release
- the public source code in this repository;
- modifications and redistributions made under AGPL-3.0 terms;
- research and open-source use consistent with AGPL-3.0.

### Not automatically granted by the public release
- trademark use of **Phionyx**;
- certification or endorsement by Phionyx Research;
- commercial warranty/support commitments;
- custom enterprise deployment terms;
- separate commercial patent or licensing agreements beyond the AGPL framework.

---

## 6. Commercial licensing path

Organizations that need different terms may request a commercial license from Phionyx Research.

Typical reasons include:

- proprietary embedding;
- closed-source distribution;
- internal legal policy against AGPL deployment;
- enterprise procurement requirements;
- support and contractual assurance needs.

Contact: **founder@phionyx.ai**

---

## 7. Practical interpretation

### If you are a researcher or open-source developer
You may use the SDK under AGPL-3.0.

### If you modify the SDK and deploy it as a network service
You must comply with AGPL-3.0 obligations.

### If you want to integrate the SDK into a proprietary offering without AGPL obligations
You need a separate commercial license.

### If you want to use the Phionyx name, claim certification, or obtain enterprise assurances
You need separate permission or agreement.

---

## 8. No legal advice

This document is a practical licensing summary, not legal advice.  
The legally controlling terms for the open-source release are those of the **GNU Affero General Public License v3.0**.  
Commercial rights, if any, exist only if granted through a separate written agreement by Phionyx Research.
