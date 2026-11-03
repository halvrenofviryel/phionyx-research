# Local candidate publication checklist

The packet is prepared for review. Publication and outreach require the owner's
explicit approval and have not been performed. Technical readiness is distinct
from external participation or adoption.

- [x] Exact K2, D, K3, beta.1 release and Phionyx base pins recorded.
- [x] Required source is in the local Git bundle; no inaccessible source URL.
- [x] Separate source lanes; no combined AIREP candidate or F integration.
- [x] 46 K3 wheels and 14 frozen K2 dependency artifacts have hashes, original
  bytes, source provenance, package metadata and license/notice copies.
- [x] Packet inputs are covered by MANIFEST.json; dependencies use frozen locks.
- [x] Blank external template and separate producer/consumer/reproduction roles.
- [x] No LLM, credentials, remote upload, private oracle or original host path
  is needed to execute the packet.
- [x] K3 raw-event, artifact, exact code-guard and NOT_EVALUATED traceability.
- [x] K2 and D plus K3 complete publication-review inventories and diffs.
- [ ] Owner approves publishing the exact reviewed candidate and bundled data.
- [ ] External reproduction or independent implementation evidence is supplied
  and reviewed. Until then the status is NOT_EVALUATED.

The measured clean-sandbox result and code revision are recorded separately in
`reports/external-replication/RESULTS.md` in the package repository. Run this
optional validation yourself on Linux with bubblewrap available:

```sh
python3 validate_offline.py --node /path/to/node-20.19.6 --out /tmp/k5-clean-validation
```

The validator mounts only `/usr`, that Node binary, this packet read-only and
fresh scratch storage. It creates new mount, PID, user and network namespaces,
clears the environment, and records the boundary probe, commands and logs.
The original single-command runner remains `python3 run.py --experiment all
--out /tmp/airep-reproduction` and does not require bubblewrap.
