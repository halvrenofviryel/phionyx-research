# Requirement mapping

All references are to the SHA-pinned -02 source; PROFILE.json freezes experimental choices.

| Category | Required distinction | Draft sections | Split counts |
|---|---|---|---|
| 01 | issuer emission without target delivery | 5.4, 5.5, 6.1 | 1 development + 1 holdout |
| 02 | missing issuer observation | 5.4, 6.5 | 1 development + 1 holdout |
| 03 | unclosed required target resolution | 4.2, 5.11, 6.4 | 1 development + 1 holdout |
| 04 | receiver correlation without confirmation | 5.5, 5.11, 6.1 | 1 development + 1 holdout |
| 05 | target or content substitution | 5.1, 5.2, 5.5, 5.10 | 1 development + 1 holdout |
| 06 | partial delivery and outcome adaptive exclusion | 4.2, 5.11, 6.2 | 1 development + 1 holdout |
| 07 | valid signed receipt without enforcement | 5.6, 5.13 | 1 development + 1 holdout |
| 08 | enforcement without effect observation | 4.4, 4.5, 5.7 | 1 development + 1 holdout |
| 09 | control race and inflight execution | 5.9, 9.4 | 1 development + 1 holdout |
| 10 | timeout is unknown not failure | 5.8, 6.1, 6.5 | 1 development + 1 holdout |
| 11 | incomplete population | 5.10, 5.11, 6.4 | 1 development + 1 holdout |
| 12 | intermediary semantic change with intact envelope | 5.13, 5.16, 6.6 | 1 development + 1 holdout |

Every case also preserves named claim scope, evidence qualification and known nonclaims under §§5.13/6.6. Population, receiver-record and obligation accounting are separately asserted in the author oracle. Native signature validity is an author-verified synthetic fact in category 7, outside evaluator crypto functionality.
