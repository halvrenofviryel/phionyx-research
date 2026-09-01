# Fixtures

Fixtures relevant to `draft-abak-agent-control-delivery-evidence`.

Nothing here is a conformance suite. `-00` Appendix "Minimum Conformance Cases"
lists sixteen cases a conforming profile *should* publish test vectors for; no
such vector set has been published by this work area.

---

## Contributed fixture — freeze race with multiple required targets

| Field | Value |
|---|---|
| File | `contributed/agent-control-delivery-freeze-race.v1.json` |
| `fixture_id` | `freeze-after-provider-entry-with-multiple-required-targets` |
| `@version` | `agent-control-delivery-conformance-fixture.v1` |
| `status` (in file) | `proposed-format-neutral-fixture` |
| Contributor | **Iman Schrock / EMILIA Protocol** (`team@emiliaprotocol.ai`) |
| Contributed in | <https://mailarchive.ietf.org/arch/msg/scitt/YcoTPgdpSl2RNWvcsB1p3c4VpAM/> |
| Attachment retrieved from | <https://mailarchive.ietf.org/arch/msg/scitt/YcoTPgdpSl2RNWvcsB1p3c4VpAM/2/> |
| Expected SHA-256 (stated by the contributor) | `2d8faa1b64b8a73fd0bf81b21889bbf726cbfb324af099b700499627af84203a` |
| Retrieved SHA-256 | `2d8faa1b64b8a73fd0bf81b21889bbf726cbfb324af099b700499627af84203a` — **exact match** |
| Size | 6212 bytes |
| Provenance clarification | <https://mailarchive.ietf.org/arch/msg/scitt/5J5i8Y6w3WkzewIzH23oMPpb9cI/> |

The attachment was downloaded mechanically from the IETF mail archive and its
digest matched the contributor's stated value exactly, so it is stored here
**unchanged**. It was not reconstructed, reformatted, or re-serialized. See
`contributed/PROVENANCE.md`.

### What the contributor says it is

Per message H, the fixture is format-neutral and marked as *proposed*, **not**
as an implementation of the draft's model. It combines two boundaries raised in
the review: the freeze binds a closed required-target set with one disposition
per instruction-target obligation; `O1` crosses provider entry before `EP-A`
applies the freeze; `O2` is refused after application.

The contributor states the expected result as: `CONFIRMED`/`APPLIED` for `EP-A`
and `UNCONFIRMED`/`UNKNOWN` for `EP-B`; the parent instruction is not fully
confirmed and cannot support `PASS`; `O1` remains consumed or in flight with an
unknown external effect pending authenticated reconciliation; and blocking `O2`
at `EP-A` does not prove every dispatch path was closed.

The fixture's `related_work` field names `draft-schrock-action-evidence-boundary-04`,
`draft-schrock-ep-revocation-statement-01`, and
`draft-schrock-ep-outcome-binding-00`, which the contributor describes as making
this a composition case rather than a claim that one layer proves the next.

The fixture also sets `required_target_population.closed_for_this_fixture: true`
alongside `enumeration_completeness_independently_proven: false` — the
distinction the author's public response singled out as not currently
represented strongly enough in `-00`.

### Provenance rules that apply

Stated by the contributor in the provenance clarification message and binding
here:

- **Unchanged use** → keep the original fixture ID and SHA-256 (what this
  directory does).
- **Adapted use** → new fixture ID, record the original fixture ID and digest as
  provenance, credit EMILIA Protocol.
- The **original contributed fixture stays pinned to AEB `-04`**, even though
  AEB is now published at `-05`. A derived case or `-01` related-work text may
  reference the current AEB revision.

No licence terms were stated by the contributor and none is asserted here. See
`../RIGHTS_AND_PROVENANCE.md`.

---

## Derivative fixtures

None. No derivative of the contributed fixture has been created. If one is
created later it must follow the derivative rules in
`../RIGHTS_AND_PROVENANCE.md` §4 — new ID, recorded source ID and digest,
contributor credit.
