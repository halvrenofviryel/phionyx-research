"""Known-data condition repair. Never loads an oracle or branches on case IDs.

Native state/qualification and reconciliation remain the frozen evaluator's.
See CONTRACT.md for v2 causal diagnostics and the deliberate oracle difference.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path

FROZEN = Path(__file__).resolve().parents[1] / 'acder02-control-benchmark'
SOURCE_HASH = '3d14d8c60a3510af66bf17d4245bc99cbb8bef159b8a18f3fe8ec2305e4231bd'
source = FROZEN / 'src/evaluate.py'
if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_HASH:
    raise RuntimeError('Frozen evaluator source changed')
spec = importlib.util.spec_from_file_location('k1_frozen_evaluator', source)
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)


class Evidence(frozen.Evidence):
    def query(self, q):
        kind, scope = q['kind'], q['scope']
        if kind in ('all_required_delivery', 'complete_mediation'):
            cutoff = scope.get('cutoff', self.cutoff['time'])
            clock = scope.get('clock_id', self.cutoff['clock_id'])
            if isinstance(cutoff, dict):
                clock, cutoff = cutoff['clock_id'], cutoff['time']
            if {'time': cutoff, 'clock_id': clock} != self.cutoff:
                case = copy.deepcopy(self.case)
                case['population']['cutoff'] = {'time': cutoff, 'clock_id': clock}
                return Evidence(case, self.profile).query(q)
        result = super().query(q)
        conditions = set(result['conditions'])
        details = []

        def cause(code, refs, **context):
            details.append({'condition': code, 'evidence_refs': sorted(set(refs)), **context})

        iid = q['subject'].get('instruction_id')
        if kind in ('all_required_delivery', 'complete_mediation'):
            ids = q['subject'].get('instruction_ids', [iid] if iid else self.expected)
            conditions.discard('unconfirmed_required_target')
            for obligation in self.obligations:
                instruction_id, target = obligation['instruction_id'], obligation['target_id']
                if instruction_id not in ids:
                    continue
                group = [r for r in self.records if r['p'].get('kind') == 'receiver_observation'
                         and self.correlated(r, instruction_id, target) and self.eligible(r)]
                context = {'instruction_id': instruction_id, 'target_id': target,
                           'disposition': obligation['disposition']}
                if not self.receipt(instruction_id, target):
                    cause('missing_receiver_observation', ['input:population'], **context)
                # Collect simultaneously applicable causes, not only the precedence winner.
                for r in group:
                    refs = ['record:' + r['id']]
                    if self.receiver_invalid(r):
                        cause('invalid_receiver_record', refs, **context)
                    if r['integrity'] and r['p'].get('content_sha256') not in (
                            None, self.instructions[instruction_id]['content_sha256']):
                        cause('governed_content_substitution', refs, **context)
                # Wrong-target evidence is not receipt for this obligation. Keep its reference
                # as a diagnostic, without claiming the other target's record is itself invalid.
                for r in self.records:
                    p = r['p']
                    ins = self.instructions[instruction_id]
                    if (p.get('kind') == 'receiver_observation' and r['integrity']
                        and p.get('instruction_id') == instruction_id
                        and p.get('identity_scope') == ins['identity_scope']
                        and p.get('attempt_id') == self.profile['receiver_success']['attempt_id']
                        and self.eligible(r) and p.get('target_id') is not None
                        and p['target_id'] not in self.targets[instruction_id]
                        and not self.receipt(instruction_id, target)):
                        cause('other_target_observation', ['record:' + r['id']], **context)
            conditions.update(d['condition'] for d in details)

        if kind == 'enforcement_applied':
            target = scope.get('target_id')
            sources = [r for r in self.candidates('enforcement', iid, target, scope)
                       if r['p'].get('boundary_id') == scope.get('boundary_id', 'target-entry')
                       and type(r['p'].get('effective_time')) in (int, float)
                       and r['p']['effective_time'] == scope.get('effective_time', r['p']['effective_time'])
                       and r['p'].get('outcome') in ('APPLIED', 'REFUSED', 'NO_EFFECT', 'UNKNOWN')]
            source_ids = {r['id'] for r in sources}
            for r in sources:
                if r['p']['outcome'] != 'APPLIED':
                    cause('source_state_does_not_establish_applied', ['record:' + r['id']],
                          native_outcome=r['p']['outcome'])
            for transform in self.candidates('transformation', iid, target, scope):
                if transform['p'].get('source_record_id') not in source_ids:
                    continue
                semantic_query = copy.deepcopy(q)
                semantic_query['kind'] = 'semantic_preservation'
                semantic_query['scope']['transformation_record_id'] = transform['id']
                semantic = super().query(semantic_query)
                if 'semantic_mapping_not_lossless' in semantic['conditions']:
                    cause('semantic_mapping_not_lossless', ['record:' + transform['id'],
                          'record:' + transform['p']['source_record_id']],
                          semantic_state=semantic['state'])
            # Mapping loss does not refute a directly evidenced native APPLIED fact.
            # It remains visible in cause_details even for that positive native claim.
            if result['state'] != 'SUPPORTED':
                conditions.update(d['condition'] for d in details)
        result['conditions'] = sorted(conditions)
        result['cause_details'] = sorted(details, key=lambda d: repr(sorted(d.items())))
        result['evidence_refs'] = sorted(set(result['evidence_refs']) |
                                         {ref for d in details for ref in d['evidence_refs']})
        return result


def evaluate(case, profile):
    if len({r['record_id'] for r in case['records']}) != len(case['records']):
        raise ValueError('duplicate envelope record_id')
    result = Evidence(case, profile).acder()
    result['condition_contract'] = 'acder02-condition-preservation-v2'
    return result
