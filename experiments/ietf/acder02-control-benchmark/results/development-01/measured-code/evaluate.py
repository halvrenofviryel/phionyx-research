#!/usr/bin/env python3
"""Three preregistered synthetic-evidence comparators; never reads an oracle.

The profile's VERIFIED bindings are stipulated fixture trust, not cryptography.
No case ID, filename, split, category or expected answer controls a decision.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def answer(q, state, conditions=(), refs=(), reason='BOUNDED_EVIDENCE', conditional=False):
    qualification = {'SUPPORTED': 'FULLY_SUPPORTED', 'REFUTED': 'NOT_SUPPORTED',
                     'INDETERMINATE': 'CONDITIONALLY_SUPPORTED' if conditional else 'NOT_SUPPORTED',
                     'NOT_EVALUATED': None, 'NOT_APPLICABLE': None}[state]
    return {'claim_id': q['claim_id'], 'kind': q['kind'], 'subject': q['subject'],
            'scope': q['scope'], 'state': state, 'qualification': qualification,
            'conditions': sorted(set(conditions)), 'reason_codes': [reason],
            'evidence_refs': sorted(set(refs))}


class Evidence:
    def __init__(self, case, profile):
        self.case, self.profile = case, profile
        if case['profile_id'] != profile['profile_id']:
            raise ValueError('unknown profile')
        self.population = case['population']
        self.instructions = {x['instruction_id']: x for x in case['instructions']}
        self.duplicate_instructions = len(self.instructions) != len(case['instructions'])
        self.records = []
        for envelope in case['records']:
            try:
                payload = json.loads(envelope['payload_utf8'])
                if not isinstance(payload, dict):
                    payload = {}
            except (ValueError, TypeError):
                payload = {}
            self.records.append({'id': envelope['record_id'], 'p': payload,
                                 'integrity': digest(envelope['payload_utf8']) == envelope['payload_sha256'],
                                 'raw': envelope['payload_utf8']})
        self.by_id = {r['id']: r for r in self.records}
        self.cutoff = self.population['cutoff']
        self.targets, self.bad_exclusions = {}, set()
        self.accounting = dict(total=0, with_obligations=0, terminal_empty=0,
                               all_excluded=0, target_resolution_unclosed=0)
        self.expected = sorted(set(self.population['manifest_instruction_ids']))
        for iid in self.expected:
            self.accounting['total'] += 1
            ins = self.instructions.get(iid)
            if not ins or ins['resolution']['status'] != 'CLOSED':
                self.accounting['target_resolution_unclosed'] += 1
                self.targets[iid] = []
                continue
            res = ins['resolution']
            excluded = set()
            rule = self.population['exclusion_rule']
            for item in res['excluded']:
                if (item.get('rule_id') == rule.get('rule_id') and
                    item.get('rule_version') == rule.get('version') and
                    item.get('input_basis') in rule.get('permitted_inputs', []) and
                    isinstance(item.get('applied_time'), (float, int)) and
                    item['applied_time'] <= rule.get('frozen_time', float('-inf')) and
                    rule.get('evidence_available') is True):
                    excluded.add(item['target_id'])
                else:
                    self.bad_exclusions.add(iid)
            self.targets[iid] = sorted(set(res['candidates']) - excluded)
            if self.targets[iid]:
                self.accounting['with_obligations'] += 1
            elif res['candidates']:
                self.accounting['all_excluded'] += 1
            else:
                self.accounting['terminal_empty'] += 1
        self.obligations, self.receiver_classes = [], {}
        self._reconcile()

    def authority(self, r):
        p = r['p']; binding = self.profile['observers'].get(p.get('observer_id'), {})
        targets = p.get('target_ids', [p.get('target_id')])
        if (p.get('kind') not in binding.get('kinds', []) or
            p.get('boundary_id') not in binding.get('boundaries', []) or
            not all(t in binding.get('targets', []) for t in targets)):
            return 'UNRESOLVED'
        return binding.get('authority', 'UNRESOLVED')

    def eligible(self, r, scope=None):
        p = r['p']; scope = scope or self.cutoff
        cutoff = scope.get('cutoff', scope.get('time', self.cutoff.get('time')))
        clock = scope.get('clock_id', self.cutoff.get('clock_id'))
        if isinstance(cutoff, dict):
            clock = cutoff.get('clock_id', clock); cutoff = cutoff['time']
        return (isinstance(p.get('time'), (int, float)) and not isinstance(p.get('time'), bool)
                and p.get('clock_id') == clock and p['time'] <= cutoff)

    def valid(self, r, iid=None, target=None, scope=None, kind=None):
        p = r['p']; ins = self.instructions.get(iid or p.get('instruction_id'))
        return bool(r['integrity'] and ins and self.eligible(r, scope)
                    and self.authority(r) != 'UNRESOLVED'
                    and p.get('instruction_id') == ins['instruction_id']
                    and p.get('identity_scope') == ins['identity_scope']
                    and p.get('content_sha256') == ins['content_sha256']
                    and p.get('attempt_id') == self.profile['receiver_success']['attempt_id']
                    and (target is None or p.get('target_id') == target)
                    and (kind is None or p.get('kind') == kind))

    def candidates(self, kind, iid=None, target=None, scope=None):
        return [r for r in self.records if self.valid(r, iid, target, scope, kind)]

    def issuer(self, iid, target=None, scope=None):
        return [r for r in self.candidates('issuer_emission', iid, scope=scope)
                if r['p'].get('outcome') == 'EMITTED'
                and r['p'].get('boundary_id') == 'issuer-egress'
                and (target is None or target in r['p'].get('target_ids', []))]

    def correlated(self, r, iid, target):
        p = r['p']; ins = self.instructions[iid]
        return (p.get('instruction_id') == iid and p.get('target_id') == target
                and p.get('identity_scope', ins['identity_scope']) == ins['identity_scope']
                and p.get('attempt_id', 'attempt-1') == self.profile['receiver_success']['attempt_id'])

    def receiver_invalid(self, r):
        p = r['p']
        return (not r['integrity'] or any(k not in p for k in self.profile['required_receiver_fields'])
                or p.get('boundary_id') != 'target-entry'
                or not isinstance(p.get('time'), (int, float)))

    def receipt(self, iid, target, scope=None):
        return [r for r in self.candidates('receiver_observation', iid, target, scope)
                if not self.receiver_invalid(r) and r['p'].get('outcome') == 'RECEIVED']

    def _reconcile(self):
        receivers = [r for r in self.records if r['p'].get('kind') == 'receiver_observation']
        for iid in self.expected:
            for target in self.targets[iid]:
                group = [r for r in receivers if self.correlated(r, iid, target)]
                ins = self.instructions[iid]
                subst = [r for r in group if r['integrity'] and
                         r['p'].get('content_sha256') not in (None, ins['content_sha256'])]
                wellformed = [r for r in group if not self.receiver_invalid(r)
                              and self.valid(r, iid, target)]
                conflict = len({r['p'].get('outcome') for r in wellformed}) > 1
                invalid = any(self.receiver_invalid(r) for r in group)
                failed = [r for r in self.candidates('failure', iid, target)
                          if r['p'].get('outcome') in ('FAILED', 'REJECTED', 'REFUSED')]
                unresolved = any(self.authority(r) == 'UNRESOLVED' for r in group)
                if subst: disposition = 'SUBSTITUTION'
                elif conflict: disposition = 'CONFLICT'
                elif invalid: disposition = 'INVALID'
                elif failed: disposition = 'EXPLICIT_FAILURE'
                elif not self.issuer(iid, target) or unresolved: disposition = 'INDETERMINATE'
                elif self.receipt(iid, target): disposition = 'CONFIRMED'
                else: disposition = 'UNCONFIRMED'
                self.obligations.append({'instruction_id': iid, 'target_id': target, 'disposition': disposition})
                seen = set()
                for r in group:
                    if r in subst: category = 'substitution'
                    elif conflict and r in wellformed: category = 'conflict'
                    elif self.receiver_invalid(r): category = 'invalid'
                    elif r['raw'] in seen: category = 'duplicate'
                    else: category = 'matched'
                    self.receiver_classes[r['id']] = category
                    seen.add(r['raw'])
        for r in receivers:
            self.receiver_classes.setdefault(r['id'], 'orphan')
        self.obligation_counts = {'total': len(self.obligations),
                                 **{s: sum(x['disposition'] == s for x in self.obligations)
                                    for s in self.profile['disposition_precedence']}}
        self.receiver_counts = {'total': len(receivers),
                                **{s: sum(v == s for v in self.receiver_classes.values())
                                   for s in self.profile['receiver_accounting_precedence']}}
        missing_members = set(self.expected) != set(self.population['included_instruction_ids'])
        positive = any(o['disposition'] in ('SUBSTITUTION', 'CONFLICT', 'INVALID', 'EXPLICIT_FAILURE')
                       for o in self.obligations) or bool(self.bad_exclusions) or missing_members or self.duplicate_instructions
        closed = (self.accounting['target_resolution_unclosed'] == 0 and
                  self.population['inclusion_rule'].get('evidence_available') is True and
                  self.population['exclusion_rule'].get('evidence_available') is True)
        self.structural = ('FAIL' if positive else 'PASS' if closed and self.obligations and
                           all(o['disposition'] == 'CONFIRMED' for o in self.obligations) else 'INCONCLUSIVE')

    def query(self, q):
        kind, subject, scope = q['kind'], q['subject'], q['scope']
        iid, target = subject.get('instruction_id'), scope.get('target_id')
        refs = []
        if kind == 'envelope_integrity':
            records = [self.by_id.get(rid) for rid in subject['record_ids']]
            if any(r is None for r in records): return answer(q, 'INDETERMINATE', reason='NAMED_RECORD_MISSING')
            return answer(q, 'SUPPORTED' if records and all(r['integrity'] for r in records) else 'REFUTED',
                          refs=['record:' + r['id'] for r in records], reason='PAYLOAD_BYTES_ONLY')
        if kind in ('all_required_delivery', 'complete_mediation'):
            ids = subject.get('instruction_ids', [iid] if iid else self.expected)
            conditions = set(); relevant = [o for o in self.obligations if o['instruction_id'] in ids]
            if set(self.expected) != set(self.population['included_instruction_ids']):
                conditions.add('population_members_missing')
            for instruction_id in ids:
                ins = self.instructions.get(instruction_id)
                if not ins:
                    conditions.add('missing_instruction_metadata'); continue
                if ins['resolution']['status'] != 'CLOSED': conditions.add('unclosed_target_resolution')
                if instruction_id in self.bad_exclusions: conditions.add('outcome_adaptive_exclusion')
                for o in relevant:
                    if o['instruction_id'] != instruction_id: continue
                    if not self.issuer(instruction_id, o['target_id']): conditions.add('missing_issuer_observation')
                    if o['disposition'] == 'SUBSTITUTION': conditions.add('governed_content_substitution')
                    elif o['disposition'] == 'INVALID': conditions.add('invalid_receiver_record')
                    elif o['disposition'] == 'UNCONFIRMED': conditions.add('unconfirmed_required_target')
                    for r in self.receipt(instruction_id, o['target_id']):
                        refs.append('record:' + r['id'])
                        if self.authority(r) == 'DECLARED_ONLY': conditions.add('authority_binding_declared_only')
                if kind == 'complete_mediation':
                    cov = ins['resolution']['coverage']
                    if cov.get('status') == 'DECLARED_ONLY': conditions.add('coverage_declared_only')
                    elif cov.get('status') != 'VERIFIED' or not cov.get('evidence_refs'): conditions.add('coverage_indeterminate')
            if not self.population['inclusion_rule'].get('evidence_available'):
                conditions.add('unverified_population_rule')
            only_conditions = conditions <= {'authority_binding_declared_only', 'coverage_declared_only'}
            ok = bool(relevant) and all(o['disposition'] == 'CONFIRMED' for o in relevant)
            return answer(q, 'SUPPORTED' if ok and not conditions else 'INDETERMINATE', conditions, refs,
                          conditional=ok and bool(conditions) and only_conditions)
        if kind == 'population_complete':
            refs = ['input:population']
            if set(self.expected) != set(self.population['included_instruction_ids']):
                return answer(q, 'REFUTED', ['population_members_missing'], refs)
            if any(i not in self.instructions for i in self.expected):
                return answer(q, 'INDETERMINATE', ['missing_instruction_metadata'], refs)
            if not self.population['inclusion_rule'].get('evidence_available'):
                return answer(q, 'INDETERMINATE', ['unverified_population_rule'], refs)
            return answer(q, 'SUPPORTED', refs=refs)
        if kind == 'ordering':
            before = self.by_id.get(scope['before_record_id']); after = self.by_id.get(scope['after_record_id'])
            if before and after and self.valid(before) and self.valid(after):
                b, a = before['p'], after['p']
                if b.get('clock_id') == a.get('clock_id'):
                    return answer(q, 'SUPPORTED' if b['time'] < a['time'] else 'REFUTED',
                                  refs=['record:' + before['id'], 'record:' + after['id']])
            return answer(q, 'INDETERMINATE', ['ordering_not_established'])
        if kind == 'semantic_preservation':
            r = self.by_id.get(scope['transformation_record_id'])
            if r and self.valid(r, iid, target, scope, 'transformation'):
                p = r['p']; mapping = p.get('state_mapping', {})
                source = self.by_id.get(p.get('source_record_id'))
                preserved = all(mapping.get(s) == s for s in self.profile['semantic_state_vocabulary'])
                preserved = preserved and source is not None and self.valid(source, iid, target)
                preserved = preserved and p.get('source_state') == source['p'].get('outcome') and p.get('destination_state') == p.get('source_state')
                return answer(q, 'SUPPORTED' if preserved else 'REFUTED',
                              [] if preserved else ['semantic_mapping_not_lossless'], ['record:' + r['id']])
            return answer(q, 'INDETERMINATE', ['semantic_mapping_not_lossless'])
        if kind == 'issuer_dispatched':
            candidates = self.issuer(iid, scope=scope); missing = 'missing_issuer_observation'
        elif kind == 'receiver_receipt':
            candidates = self.receipt(iid, target, scope); missing = 'missing_receiver_observation'
            ins = self.instructions.get(iid, {})
            correlated = [r for r in self.records if r['p'].get('kind') == 'receiver_observation'
                          and iid in self.instructions and self.correlated(r, iid, target)]
            if not candidates:
                if any(r['integrity'] and r['p'].get('content_sha256') not in (None, ins.get('content_sha256')) for r in correlated):
                    missing = 'governed_content_substitution'
                elif any(self.receiver_invalid(r) for r in correlated): missing = 'invalid_receiver_record'
        elif kind == 'enforcement_applied':
            candidates = [r for r in self.candidates('enforcement', iid, target, scope)
                          if r['p'].get('boundary_id') == scope.get('boundary_id', 'target-entry')
                          and isinstance(r['p'].get('effective_time'), (int, float))
                          and r['p']['effective_time'] == scope.get('effective_time', r['p']['effective_time'])
                          and r['p'].get('outcome') in ('APPLIED', 'REFUSED', 'NO_EFFECT', 'UNKNOWN')]
            positives = [r for r in candidates if r['p']['outcome'] == 'APPLIED']
            negatives = [r for r in candidates if r['p']['outcome'] in ('REFUSED', 'NO_EFFECT')]
            if negatives and not positives:
                return answer(q, 'REFUTED', ['source_state_does_not_establish_applied'], ['record:' + r['id'] for r in negatives])
            if negatives and positives:
                return answer(q, 'INDETERMINATE', ['source_state_does_not_establish_applied'], reason='CONTRADICTORY_NATIVE_ASSERTIONS')
            if candidates and not positives:
                conditions = ['source_state_does_not_establish_applied']
                transformations = [r for r in self.candidates('transformation', iid, target, scope)
                                   if r['p'].get('source_record_id') in {x['id'] for x in candidates}]
                if any(any(r['p'].get('state_mapping', {}).get(s) != s
                           for s in self.profile['semantic_state_vocabulary']) for r in transformations):
                    conditions.append('semantic_mapping_not_lossless')
                return answer(q, 'INDETERMINATE', conditions, ['record:' + r['id'] for r in candidates])
            candidates = positives; missing = 'missing_enforcement_observation'
        elif kind == 'execution_observed':
            candidates = [r for r in self.candidates('boundary_crossing', iid, target, scope)
                          if r['p'].get('boundary_id') == scope.get('boundary_id', 'provider-entry')
                          and r['p'].get('operation_id') == scope.get('operation_id')
                          and r['p'].get('outcome') == 'ENTERED']
            missing = None
        elif kind == 'effect_observed':
            candidates = [r for r in self.candidates('effect', iid, target, scope)
                          if r['p'].get('operation_id') == scope.get('operation_id')
                          and r['p'].get('predicate_id') == scope.get('predicate_id')
                          and r['p'].get('window') == scope.get('window') and r['p'].get('method')]
            negatives = [r for r in candidates if r['p'].get('result') == 'NO_EFFECT']
            positives = [r for r in candidates if r['p'].get('result') == 'EFFECT_OBSERVED']
            if negatives and not positives:
                return answer(q, 'REFUTED', refs=['record:' + r['id'] for r in negatives])
            if negatives and positives:
                return answer(q, 'INDETERMINATE', ['missing_effect_observation'], reason='CONTRADICTORY_NATIVE_ASSERTIONS')
            # An exact, accepted entry observation is a positive counterexample
            # to the explicitly requested no-entry predicate in that window.
            # Absence of entry observations can never establish the predicate.
            if not positives and scope.get('predicate_id') == 'no_provider_entry':
                window = scope.get('window', [])
                entries = [r for r in self.candidates('boundary_crossing', iid, target, scope)
                           if r['p'].get('operation_id') == scope.get('operation_id')
                           and r['p'].get('boundary_id') == 'provider-entry'
                           and r['p'].get('outcome') == 'ENTERED' and len(window) == 2
                           and window[0] <= r['p']['time'] <= window[1]]
                if entries:
                    return answer(q, 'REFUTED', refs=['record:' + r['id'] for r in entries],
                                  reason='POSITIVE_COUNTEREXAMPLE_WITHIN_EXACT_WINDOW')
            missing = 'effect_scope_mismatch' if not positives and self.candidates('effect', iid, target, scope) else 'missing_effect_observation'
            candidates = positives
        else:
            return answer(q, 'NOT_EVALUATED', reason='OUTSIDE_PROFILE')
        if candidates:
            conditions = ['authority_binding_declared_only'] if any(self.authority(r) == 'DECLARED_ONLY' for r in candidates) else []
            return answer(q, 'INDETERMINATE' if conditions else 'SUPPORTED', conditions,
                          ['record:' + r['id'] for r in candidates], conditional=bool(conditions))
        return answer(q, 'INDETERMINATE', [missing] if missing else [], reason='MANDATORY_EVIDENCE_MISSING')

    def acder(self):
        claims = [self.query(q) for q in self.case['queries']]
        conditions = set()
        # This aggregate asserts the bounded structural RESULT, including FAIL
        # or INCONCLUSIVE. It does not assert successful delivery. Missing delivery
        # evidence remains explicit in the independently scoped claim rows.
        relevant_receipts = [r for r in self.records if self.receiver_classes.get(r['id']) == 'matched']
        if any(self.authority(r) == 'DECLARED_ONLY' for r in relevant_receipts): conditions.add('authority_binding_declared_only')
        qualification = 'CONDITIONALLY_SUPPORTED' if conditions else 'FULLY_SUPPORTED'
        return {'case_id': self.case['case_id'], 'claims': claims, 'obligations': self.obligations,
                'instruction_accounting': self.accounting, 'obligation_counts': self.obligation_counts,
                'receiver_record_counts': self.receiver_counts, 'structural_result': self.structural,
                'aggregate_claim': {'fact': self.profile['aggregate_claim']['fact'],
                                    'scope': {'manifest_id': self.population['manifest_id'],
                                              'instruction_ids': self.expected, 'target_sets': self.targets,
                                              'cutoff': self.cutoff, 'profile_id': self.profile['profile_id']},
                                    'qualification': qualification, 'conditions': sorted(conditions)}}


def evaluate(case, profile, comparator):
    if comparator == 'acder_bounded': return Evidence(case, profile).acder()
    applicable = profile['baseline_contracts'][comparator]['applicable_kinds']
    records = {r['record_id']: r for r in case['records']}
    payloads = []
    if comparator == 'naive_ack':
        for r in case['records']:
            try:
                p = json.loads(r['payload_utf8'])
                if isinstance(p, dict): payloads.append((r['record_id'], p))
            except (ValueError, TypeError):
                pass
    claims = []
    for q in case['queries']:
        if q['kind'] not in applicable:
            claims.append(answer(q, 'NOT_APPLICABLE', reason='OUTSIDE_DECLARED_CONTRACT')); continue
        if comparator == 'integrity_only':
            named = [records.get(rid) for rid in q['subject']['record_ids']]
            if any(r is None for r in named):
                claims.append(answer(q, 'INDETERMINATE', reason='NAMED_RECORD_MISSING'))
            else:
                ok = bool(named) and all(digest(r['payload_utf8']) == r['payload_sha256'] for r in named)
                claims.append(answer(q, 'SUPPORTED' if ok else 'REFUTED',
                                     refs=['record:' + r['record_id'] for r in named], reason='PAYLOAD_BYTES_ONLY'))
            continue
        ids = q['subject'].get('instruction_ids', [q['subject'].get('instruction_id')])
        acknowledgements = [rid for rid, p in payloads if p.get('instruction_id') in ids
                            and p.get('kind') in ('transport_ack', 'receiver_observation')
                            and p.get('outcome') in ('ACCEPTED', 'QUEUED', 'RECEIVED')]
        claims.append(answer(q, 'SUPPORTED' if acknowledgements else 'INDETERMINATE',
                             refs=['record:' + rid for rid in acknowledgements], reason='EXPLICIT_NAIVE_ACK_PROMOTION'))
    return {'case_id': case['case_id'], 'claims': claims}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--evidence-dir', type=Path, required=True)
    ap.add_argument('--profile', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    profile = json.loads(args.profile.read_text())
    # Deliberately traverse only evidence.json; oracle/truth files are unnecessary.
    cases = [json.loads(p.read_text()) for p in sorted(args.evidence_dir.rglob('evidence.json'))]
    if not cases or len({c['case_id'] for c in cases}) != len(cases):
        raise ValueError('empty corpus or duplicate case IDs')
    result = {name: [evaluate(c, profile, name) for c in cases] for name in profile['baseline_contracts']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
