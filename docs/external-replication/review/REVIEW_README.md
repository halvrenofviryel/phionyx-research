# Publication review lanes

This candidate carries two exact source refs rather than a merged AIREP source
tree. Their bundle makes locally unpublished code available without a fabricated
upstream URL. There is no new combined AIREP commit to report.

- `k2/`: public AIREP main `075aff5610731736405951ecf3b7c4bfc3cc0f07`
  → K2 `ea1f39a6da72639a73e601918a6c8bc87bff1d77`.
- `d-plus-k3/`: the same public main → K3
  `76ecce0b378a6b391850795abf45fb6aca8e1d6b`, explicitly including D
  `0130fcf8e7d70a0f9c4f977957e5de76ca8ef689` and its source/tests/docs.

Each lane contains a complete changed-file inventory with exact bytes/hashes,
a full compressed diff, and a readable implementation-focused diff. The full
diff reports binary changes; the actual binary bytes and exact Git trees are
inside `bundles/airep-sources.bundle`. D also has its own full diff. Excluded
historical report bodies remain in the full diff/inventory/source bundle; the
implementation-focused diff is not the entire approval scope.

Reviewer checks: source/schema scope, preserved negative results and limitations,
dependency/license notices, historical paths and metadata, local signing/test-key
policy, no fabricated public candidate URL, and explicit absence of F. Frozen
packages have not been rewritten or sanitized silently. K3 review must include D.

Technical packet readiness and permission to publish are separate. No push, PR,
issue, email, release or IETF submission is authorized by this local review packet.
