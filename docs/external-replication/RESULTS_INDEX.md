# Result index and current boundary

| Entry | Pinned local evidence | Status and limit |
|---|---|---|
| K2 frozen source | `ea1f39a6…`; `interop/same-version/v0.2.0-beta.1/RESULTS.md` inside bundled source | 28 current harness tests, original 20-test measurement preserved, eight negative controls, beta 56/56; same first-party reference family |
| D + K3 frozen source | `76ecce0b…`; `reports/langgraph/RESULTS.md` inside bundled source | 13 tests, six real local scenarios, beta 56/56, bounded cooperative pause; D included |
| K5 author-controlled clean-room replay | Repository `reports/external-replication/` alongside this packet | Separately recorded package validation; no external participant inferred |
| External producer/consumer/reproduction/product use | Blank submission template | **NOT_EVALUATED** |
| Broader K1, A/B3/C/E/F packet lanes | Not included in this delivery | PENDING or explicitly excluded; no invented PASS |

Source bundle refs and full SHA values are in [protocol-pins.json](protocol-pins.json).
The replay writes `OUTPUT/results/k2/run_record.json` and
`OUTPUT/results/k3/run_record.json`, plus a top-level command/output hash record.
Recorded historical absolute paths are retained verbatim in frozen sources and
review diffs. The runner never dereferences those paths.

See [PLAN_COVERAGE.md](PLAN_COVERAGE.md) for remaining K2/K3 scope limitations.
In particular, this delivery does not claim the entire original K2/K3 wish list
was measured. It packages their completed bounded results without rewriting them.
