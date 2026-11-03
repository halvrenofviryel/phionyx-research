# Bounded control-evidence comparison

This experiment asks a narrow question: when evidence contains an acknowledgement
but does not establish delivery to every target, enforcement or effect, which
claims does a comparator support?

On the first frozen holdout run, the deliberately naive ACK-promotion rule made
16 unsupported stronger assertions on the 18 queries shared with the bounded
ACDER-derived evaluator. The bounded evaluator made 0 on that shared subset and
recovered all 31 evidenced claims in its own broader contract. The result is a
controlled demonstration of a specific inference failure, not a product ranking
or proof that ACDER is superior to every careful event-processing design.

## Reproduce

From this directory, with Python 3.12 on Linux:

```sh
python3 -B reproduce.py --out /tmp/acder02-control-benchmark
```

The output directory must not already exist. The command runs 44 tests and
replays all 24 synthetic cases and 321 comparator rows. It requires no network,
account, API key or paid model call.

Start review with [RESULTS.md](RESULTS.md), then read
[LIMITATIONS.md](LIMITATIONS.md), [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md)
and [REPRODUCE.md](REPRODUCE.md). Complete machine results are under `results/`.

## Claim boundary

- The 54 holdout queries come from 12 synthetic cases; they are not 54 independent
  field observations.
- The author and evaluator roles share one owner and machine. The freeze and
  access boundary support a controlled holdout, not external independence.
- The naive comparator is an explicit analytical rule, not an implementation of
  a named product, standard or state-of-the-art baseline.
- Exact holdout condition agreement is 52/54. Both differences remain in the
  frozen result, including the omitted semantic-loss condition on one enforcement
  claim.
- The evaluator implements the declared subset and synthetic profile. It does not
  establish full ACDER conformance, event truth, deployment safety or adoption.

The author bundle contains a deliberately public synthetic Ed25519 test key pair.
It has no account or issuer authority and must never be treated as an operational
credential.
