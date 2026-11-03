# Exact frozen metrics

Every rate is numerator/denominator. N/A means denominator zero. No rounding or confidence interval is used. Full 5-state confusion matrices are in results/score.json.

## development

| Comparator | Claim kind | Applicable | Unsupported support | Properly withheld | Semantic false | False rejection | Support recall | State match | Qualification | Conditions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| acder_bounded | all_required_delivery | 8 | 0/7 | 7/7 | 0/1 | 0/1 | 1/1 | 8/8 | 8/8 | 8/8 |
| acder_bounded | complete_mediation | 2 | 0/2 | 2/2 | N/A (0/0) | N/A (0/0) | N/A (0/0) | 2/2 | 2/2 | 2/2 |
| acder_bounded | effect_observed | 5 | 0/4 | 3/3 | 0/2 | 0/1 | 1/1 | 5/5 | 5/5 | 5/5 |
| acder_bounded | enforcement_applied | 4 | 0/3 | 3/3 | 0/1 | 0/1 | 1/1 | 4/4 | 4/4 | 4/4 |
| acder_bounded | envelope_integrity | 12 | N/A (0/0) | N/A (0/0) | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| acder_bounded | execution_observed | 1 | N/A (0/0) | N/A (0/0) | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| acder_bounded | issuer_dispatched | 6 | 0/1 | 1/1 | 0/5 | 0/5 | 5/5 | 6/6 | 6/6 | 6/6 |
| acder_bounded | ordering | 1 | N/A (0/0) | N/A (0/0) | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| acder_bounded | population_complete | 2 | 0/1 | N/A (0/0) | 0/2 | 0/1 | 1/1 | 2/2 | 2/2 | 2/2 |
| acder_bounded | receiver_receipt | 11 | 0/4 | 4/4 | 0/7 | 0/7 | 7/7 | 11/11 | 11/11 | 11/11 |
| acder_bounded | semantic_preservation | 1 | 0/1 | N/A (0/0) | 0/1 | N/A (0/0) | N/A (0/0) | 1/1 | 1/1 | 1/1 |
| acder_bounded | ALL_KINDS | 53 | 0/23 | 20/20 | 0/33 | 0/30 | 30/30 | 53/53 | 53/53 | 53/53 |
| integrity_only | all_required_delivery | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | complete_mediation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | effect_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | enforcement_applied | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | envelope_integrity | 12 | N/A (0/0) | N/A (0/0) | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| integrity_only | execution_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | issuer_dispatched | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | ordering | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | population_complete | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | receiver_receipt | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | semantic_preservation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | ALL_KINDS | 12 | N/A (0/0) | N/A (0/0) | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| naive_ack | all_required_delivery | 8 | 6/7 | 1/7 | 5/7 | 0/1 | 1/1 | 2/8 | 2/8 | 1/8 |
| naive_ack | complete_mediation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | effect_observed | 5 | 4/4 | 0/3 | 3/5 | 0/1 | 1/1 | 1/5 | 1/5 | 1/5 |
| naive_ack | enforcement_applied | 4 | 3/3 | 0/3 | 2/4 | 0/1 | 1/1 | 1/4 | 1/4 | 1/4 |
| naive_ack | envelope_integrity | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | execution_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | issuer_dispatched | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | ordering | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | population_complete | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | receiver_receipt | 11 | 3/4 | 1/4 | 3/10 | 0/7 | 7/7 | 8/11 | 8/11 | 7/11 |
| naive_ack | semantic_preservation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | ALL_KINDS | 28 | 16/18 | 2/17 | 13/26 | 0/10 | 10/10 | 12/28 | 12/28 | 10/28 |

## holdout

| Comparator | Claim kind | Applicable | Unsupported support | Properly withheld | Semantic false | False rejection | Support recall | State match | Qualification | Conditions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| acder_bounded | all_required_delivery | 8 | 0/7 | 7/7 | 0/1 | 0/1 | 1/1 | 8/8 | 8/8 | 7/8 |
| acder_bounded | complete_mediation | 2 | 0/1 | 1/1 | 0/1 | 0/1 | 1/1 | 2/2 | 2/2 | 2/2 |
| acder_bounded | effect_observed | 5 | 0/4 | 3/3 | 0/2 | 0/1 | 1/1 | 5/5 | 5/5 | 5/5 |
| acder_bounded | enforcement_applied | 5 | 0/3 | 2/2 | 0/3 | 0/2 | 2/2 | 5/5 | 5/5 | 4/5 |
| acder_bounded | envelope_integrity | 12 | N/A (0/0) | N/A (0/0) | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| acder_bounded | execution_observed | 1 | N/A (0/0) | N/A (0/0) | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| acder_bounded | issuer_dispatched | 6 | 0/1 | 1/1 | 0/5 | 0/5 | 5/5 | 6/6 | 6/6 | 6/6 |
| acder_bounded | ordering | 1 | 0/1 | N/A (0/0) | 0/1 | N/A (0/0) | N/A (0/0) | 1/1 | 1/1 | 1/1 |
| acder_bounded | population_complete | 2 | 0/1 | N/A (0/0) | 0/2 | 0/1 | 1/1 | 2/2 | 2/2 | 2/2 |
| acder_bounded | receiver_receipt | 11 | 0/4 | 4/4 | 0/7 | 0/7 | 7/7 | 11/11 | 11/11 | 11/11 |
| acder_bounded | semantic_preservation | 1 | 0/1 | N/A (0/0) | 0/1 | N/A (0/0) | N/A (0/0) | 1/1 | 1/1 | 1/1 |
| acder_bounded | ALL_KINDS | 54 | 0/23 | 18/18 | 0/36 | 0/31 | 31/31 | 54/54 | 54/54 | 52/54 |
| integrity_only | all_required_delivery | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | complete_mediation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | effect_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | enforcement_applied | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | envelope_integrity | 12 | N/A (0/0) | N/A (0/0) | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| integrity_only | execution_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | issuer_dispatched | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | ordering | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | population_complete | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | receiver_receipt | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | semantic_preservation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | ALL_KINDS | 12 | N/A (0/0) | N/A (0/0) | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| naive_ack | all_required_delivery | 8 | 6/7 | 1/7 | 4/7 | 0/1 | 1/1 | 2/8 | 2/8 | 1/8 |
| naive_ack | complete_mediation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | effect_observed | 5 | 4/4 | 0/3 | 4/5 | 0/1 | 1/1 | 1/5 | 1/5 | 1/5 |
| naive_ack | enforcement_applied | 5 | 3/3 | 0/2 | 3/5 | 0/2 | 2/2 | 2/5 | 2/5 | 2/5 |
| naive_ack | envelope_integrity | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | execution_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | issuer_dispatched | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | ordering | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | population_complete | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | receiver_receipt | 11 | 3/4 | 1/4 | 1/10 | 0/7 | 7/7 | 8/11 | 8/11 | 7/11 |
| naive_ack | semantic_preservation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | ALL_KINDS | 29 | 16/18 | 2/16 | 12/27 | 0/11 | 11/11 | 13/29 | 13/29 | 11/29 |

## total

| Comparator | Claim kind | Applicable | Unsupported support | Properly withheld | Semantic false | False rejection | Support recall | State match | Qualification | Conditions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| acder_bounded | all_required_delivery | 16 | 0/14 | 14/14 | 0/2 | 0/2 | 2/2 | 16/16 | 16/16 | 15/16 |
| acder_bounded | complete_mediation | 4 | 0/3 | 3/3 | 0/1 | 0/1 | 1/1 | 4/4 | 4/4 | 4/4 |
| acder_bounded | effect_observed | 10 | 0/8 | 6/6 | 0/4 | 0/2 | 2/2 | 10/10 | 10/10 | 10/10 |
| acder_bounded | enforcement_applied | 9 | 0/6 | 5/5 | 0/4 | 0/3 | 3/3 | 9/9 | 9/9 | 8/9 |
| acder_bounded | envelope_integrity | 24 | N/A (0/0) | N/A (0/0) | 0/24 | 0/24 | 24/24 | 24/24 | 24/24 | 24/24 |
| acder_bounded | execution_observed | 2 | N/A (0/0) | N/A (0/0) | 0/2 | 0/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| acder_bounded | issuer_dispatched | 12 | 0/2 | 2/2 | 0/10 | 0/10 | 10/10 | 12/12 | 12/12 | 12/12 |
| acder_bounded | ordering | 2 | 0/1 | N/A (0/0) | 0/2 | 0/1 | 1/1 | 2/2 | 2/2 | 2/2 |
| acder_bounded | population_complete | 4 | 0/2 | N/A (0/0) | 0/4 | 0/2 | 2/2 | 4/4 | 4/4 | 4/4 |
| acder_bounded | receiver_receipt | 22 | 0/8 | 8/8 | 0/14 | 0/14 | 14/14 | 22/22 | 22/22 | 22/22 |
| acder_bounded | semantic_preservation | 2 | 0/2 | N/A (0/0) | 0/2 | N/A (0/0) | N/A (0/0) | 2/2 | 2/2 | 2/2 |
| acder_bounded | ALL_KINDS | 107 | 0/46 | 38/38 | 0/69 | 0/61 | 61/61 | 107/107 | 107/107 | 105/107 |
| integrity_only | all_required_delivery | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | complete_mediation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | effect_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | enforcement_applied | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | envelope_integrity | 24 | N/A (0/0) | N/A (0/0) | 0/24 | 0/24 | 24/24 | 24/24 | 24/24 | 24/24 |
| integrity_only | execution_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | issuer_dispatched | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | ordering | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | population_complete | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | receiver_receipt | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | semantic_preservation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| integrity_only | ALL_KINDS | 24 | N/A (0/0) | N/A (0/0) | 0/24 | 0/24 | 24/24 | 24/24 | 24/24 | 24/24 |
| naive_ack | all_required_delivery | 16 | 12/14 | 2/14 | 9/14 | 0/2 | 2/2 | 4/16 | 4/16 | 2/16 |
| naive_ack | complete_mediation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | effect_observed | 10 | 8/8 | 0/6 | 7/10 | 0/2 | 2/2 | 2/10 | 2/10 | 2/10 |
| naive_ack | enforcement_applied | 9 | 6/6 | 0/5 | 5/9 | 0/3 | 3/3 | 3/9 | 3/9 | 3/9 |
| naive_ack | envelope_integrity | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | execution_observed | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | issuer_dispatched | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | ordering | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | population_complete | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | receiver_receipt | 22 | 6/8 | 2/8 | 4/20 | 0/14 | 14/14 | 16/22 | 16/22 | 14/22 |
| naive_ack | semantic_preservation | 0 | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) | N/A (0/0) |
| naive_ack | ALL_KINDS | 57 | 32/36 | 4/33 | 25/53 | 0/21 | 21/21 | 25/57 | 25/57 | 21/57 |
