# Example Profiles

Three runnable profile YAMLs covering common deployment shapes:

| File | Persona | Notable dials |
|------|---------|---------------|
| [`education.yaml`](education.yaml) | School / EdTech / tutoring | `BaseMode=SCHOOL`, `pii_mode=FULL`, `audit_level=VERBOSE`, `entropy_penalty_k=1.2`, `safety_bias=0.85` |
| [`creative_writing.yaml`](creative_writing.yaml) | Fiction, brainstorming, editorial | `entropy=0.55`, `entropy_penalty_k=0.8`, `pii_mode=PARTIAL`, `routing=BALANCED` |
| [`customer_support.yaml`](customer_support.yaml) | B2B/B2C support agents | `pii_mode=FULL`, `audit_level=VERBOSE`, `routing=COST_OPTIMIZED` |

## Why these three

They occupy three different points in the safety / freedom / cost cube:

- **Education** — strict and quiet. Strong PII scrubbing, verbose audit
  for compliance regimes (KCSIE-style retention), low entropy so the
  language stays predictable.
- **Creative writing** — the only profile that asks for *more* entropy.
  Safety gates still run; this profile only relaxes tone and physics
  dampening.
- **Customer support** — full audit, full PII scrubbing, cost-optimized
  routing because volume usually beats per-turn quality budget.

## Validate

```python
import yaml
from phionyx_core import Profile

profile = Profile.model_validate(yaml.safe_load(open("examples/profiles/education.yaml")))
print(profile.name, profile.governance.audit_level, profile.routing.llm_tier_strategy)
# education_default VERBOSE QUALITY_OPTIMIZED
```

All three files validate cleanly against `phionyx_core.Profile`.

## Dial-by-dial map

For the full surface (every field, every range), see
[`phionyx_core/profiles/schema.py`](../../phionyx_core/profiles/schema.py).
The configs here only set the dials that *differ* between profiles —
everything else falls back to the schema's documented defaults.
