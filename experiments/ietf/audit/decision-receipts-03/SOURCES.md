# Source acquisition and attribution

Every external input used for this experiment has an exact URL, resolved URL,
UTC acquisition time, byte length and SHA-256 in [sources/manifest.json](sources/manifest.json).
All retrieved documents and API responses are unmodified bytes. The normalized
draft diff and section comparison are derived local artifacts, not fetched
resources. Binary distributions remain in the ignored local `.downloads/` cache;
their manifest and hash-locked dependency list are committed.

The first sandbox urllib request to IETF was unavailable because DNS resolution
failed. Web-tool opens were also unavailable. Approved read-only network access
then retrieved the exact sources successfully. No missing response was turned
into a verified source. Git fetch succeeded independently and did not move HEAD.

The published tag is annotated: the tag-ref response names an object, and the
tag-object response names commit `699545521ec5ef479bb84e61fe7461fc79ed558c`.
The preview's commit object and README are separately pinned at
`8bb289c8b41d32c54734155fc00756231093bc2a`. README inspection verifies its role as
the Claude Code/Codex plugin preview; no runtime or store behavior is measured
from that preview. The PyPI wheel and sdist hashes match the versioned PyPI
metadata. Git blob comparison covers the wheel's Python modules, not every
packaging artifact or a source rebuild.

The [API inventory](evidence/api-inventory.json) stores hashes of installed source
modules read for the receipt APIs and the process-token explanation. Those
modules come from the pinned wheel. The unmodified original API capture is
[evidence/api_results.original.json](evidence/api_results.original.json); only
the comparison report masks non-null process-local `verified_origin` tokens.
Their originating process has exited. These files are archival observations,
never trusted verifier-result objects to reuse in a policy decision.

The original IETF documents retain their notices. Reconstructed Appendix A
decision/outcome vectors and SER -04 P1 come from documents authored by
K. Gruszka and are attributed to IETF. Their Code Components, including the
vector constants in the fixture/test code and generated `cases/fixtures/`, use
this [TLP §6.d notification](https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/):

> Copyright (c) 2026 IETF Trust and the persons identified as authors of the code.
> All rights reserved.
>
> Redistribution and use in source and binary forms, with or without modification,
> is permitted pursuant to, and subject to the license terms contained in, the
> Revised BSD License set forth in Section 4.c of the IETF Trust's Legal Provisions
> Relating to IETF Documents (https://trustee.ietf.org/license-info).

The exact corrected TLP page is pinned in the source manifest. Copies of the
proofbundle decision/outcome documentation and preview README retain the MIT
notice in `sources/proofbundle-release-LICENSE` and
`sources/proofbundle-preview-LICENSE`, each acquired at the corresponding commit.
No upstream code was modified or copied into a replacement implementation.
No endorsement by IETF or the upstream author is implied.
