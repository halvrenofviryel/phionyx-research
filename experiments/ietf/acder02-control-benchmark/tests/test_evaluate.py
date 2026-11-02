import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

PACKAGE = Path(os.environ.get('K1_PACKAGE', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(PACKAGE / 'src'))
from evaluate import evaluate, digest


def native(envelope, **changes):
    p = json.loads(envelope['payload_utf8']); p.update(changes)
    envelope['payload_utf8'] = json.dumps(p, sort_keys=True, separators=(',', ':'))
    envelope['payload_sha256'] = digest(envelope['payload_utf8'])


class EvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads((PACKAGE / 'PROFILE.json').read_text())

    def case(self, name='dev-08'):
        return json.loads((PACKAGE / 'scenarios' / 'development' / name / 'evidence.json').read_text())

    def result(self, c, comparator='acder_bounded'):
        return evaluate(c, self.profile, comparator)

    def claims(self, c, comparator='acder_bounded'):
        return {q['kind']: q for q in self.result(c, comparator)['claims']}

    def test_each_scenario_deterministic_scoped_and_conserved(self):
        roots = [PACKAGE / 'scenarios' / 'development']
        if os.environ.get('K1_TEST_INCLUDE_HOLDOUT') == '1':
            self.assertTrue((PACKAGE / 'LOGIC_FREEZE.json').exists())
            roots.append(PACKAGE / 'scenarios' / 'holdout')
        for f in sorted(f for root in roots for f in root.rglob('evidence.json')):
            c = json.loads(f.read_text())
            for baseline in self.profile['baseline_contracts']:
                with self.subTest(case=c['case_id'], baseline=baseline):
                    first = self.result(c, baseline); second = self.result(copy.deepcopy(c), baseline)
                    self.assertEqual(first, second)
                    self.assertEqual([q['claim_id'] for q in c['queries']], [q['claim_id'] for q in first['claims']])
                    for q, a in zip(c['queries'], first['claims']):
                        self.assertEqual(a['scope'], q['scope']); self.assertEqual(a['subject'], q['subject'])
                    if baseline == 'acder_bounded':
                        for key in ('instruction_accounting', 'obligation_counts', 'receiver_record_counts'):
                            counts = first[key]
                            self.assertEqual(counts['total'], sum(v for k, v in counts.items() if k != 'total'))

    def test_target_substitution_cannot_confirm_receipt(self):
        c = self.case()
        native(next(r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] == 'receiver_observation'), target_id='ep-b', observer_id='ep-b')
        result = self.result(c)
        self.assertEqual(self.claims(c)['receiver_receipt']['state'], 'INDETERMINATE')
        self.assertEqual(result['obligation_counts']['UNCONFIRMED'], 1)
        self.assertEqual(result['receiver_record_counts']['orphan'], 1)

    def test_content_substitution_retained_and_fails_structure(self):
        c = self.case()
        native(next(r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] == 'receiver_observation'), content_sha256='0' * 64)
        r = self.result(c)
        self.assertEqual(r['structural_result'], 'FAIL')
        self.assertEqual(r['obligation_counts']['SUBSTITUTION'], 1)
        self.assertNotEqual(self.claims(c)['receiver_receipt']['state'], 'SUPPORTED')

    def test_missing_receiver_is_not_failed_delivery(self):
        c = self.case()
        c['records'] = [r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] != 'receiver_observation']
        r = self.result(c)
        self.assertEqual(r['structural_result'], 'INCONCLUSIVE')
        self.assertEqual(self.claims(c)['receiver_receipt']['state'], 'INDETERMINATE')

    def test_effect_positive_then_missing_mutation(self):
        c = self.case('dev-09')
        before = {q['claim_id']: q for q in self.result(c)['claims']}
        self.assertEqual(before['q-effect-later']['state'], 'SUPPORTED')
        c['records'] = [r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] != 'effect']
        after = {q['claim_id']: q for q in self.result(c)['claims']}
        self.assertEqual(after['q-effect-later']['state'], 'INDETERMINATE')
        self.assertEqual(after['q-execution']['state'], 'SUPPORTED')

    def test_valid_signature_does_not_imply_execution(self):
        c = self.case('dev-07')
        self.assertTrue(any('signature' in r for r in c['records']))
        q = copy.deepcopy(c['queries'][1]); q.update(claim_id='mutation-execution', kind='execution_observed')
        q['scope'].update(boundary_id='provider-entry', operation_id='operation-unseen')
        c['queries'].append(q)
        claims = self.claims(c)
        self.assertEqual(claims['envelope_integrity']['state'], 'SUPPORTED')
        self.assertEqual(claims['execution_observed']['state'], 'INDETERMINATE')
        self.assertEqual(self.claims(c, 'integrity_only')['execution_observed']['state'], 'NOT_APPLICABLE')

    def test_no_ack_does_not_imply_no_delivery(self):
        c = self.case('dev-10')
        for baseline in ('naive_ack', 'acder_bounded'):
            self.assertEqual(self.claims(c, baseline)['receiver_receipt']['state'], 'INDETERMINATE')

    def test_missing_issuer_does_not_erase_receiver(self):
        c = self.case('dev-02'); r = self.result(c)
        self.assertEqual(self.claims(c)['receiver_receipt']['state'], 'SUPPORTED')
        self.assertEqual(r['obligation_counts']['INDETERMINATE'], 1)

    def test_unclosed_resolution_no_vacuous_success(self):
        r = self.result(self.case('dev-03'))
        self.assertEqual(r['obligation_counts']['total'], 0)
        self.assertEqual(r['structural_result'], 'INCONCLUSIVE')

    def test_digest_checks_exact_bytes_not_reserialization(self):
        c = self.case(); c['records'][0]['payload_utf8'] += ' '
        for b in ('integrity_only', 'acder_bounded'):
            self.assertEqual(self.claims(c, b)['envelope_integrity']['state'], 'REFUTED')

    def test_instruction_id_is_not_lookup_of_answer(self):
        c = self.case(); old = c['instructions'][0]['instruction_id']; new = 'arbitrary-renamed-identity'
        # Rename all visible references consistently; no oracle exists in this test.
        renamed = json.loads(json.dumps(c).replace(old, new))
        for r in renamed['records']: r['payload_sha256'] = digest(r['payload_utf8'])
        self.assertEqual([(x['state'], x['conditions']) for x in self.result(c)['claims']],
                         [(x['state'], x['conditions']) for x in self.result(renamed)['claims']])

    def test_positive_entry_refutes_only_exact_no_entry_window(self):
        c = self.case('dev-09')
        claims = {q['claim_id']: q for q in self.result(c)['claims']}
        self.assertEqual(claims['q-effect-earlier']['state'], 'REFUTED')
        q = next(q for q in c['queries'] if q['claim_id'] == 'q-effect-earlier')
        q['scope']['window'] = [0, 1]
        claims = {q['claim_id']: q for q in self.result(c)['claims']}
        self.assertEqual(claims['q-effect-earlier']['state'], 'INDETERMINATE')

    def test_effect_and_enforcement_scope_not_interchangeable(self):
        c = self.case()
        q = next(q for q in c['queries'] if q['kind'] == 'enforcement_applied')
        q['scope']['effective_time'] += 1
        self.assertEqual(self.claims(c)['enforcement_applied']['state'], 'INDETERMINATE')
        self.assertEqual(self.claims(c)['effect_observed']['state'], 'INDETERMINATE')

    def test_baselines_do_not_need_acder_population_reconciliation(self):
        c = self.case(); c['population'] = {}; c['instructions'] = []
        self.assertEqual(self.claims(c, 'integrity_only')['envelope_integrity']['state'], 'SUPPORTED')
        self.assertEqual(self.claims(c, 'naive_ack')['enforcement_applied']['state'], 'SUPPORTED')

    def test_aggregate_query_uses_its_own_cutoff(self):
        c = self.case('dev-07')
        q = next(q for q in c['queries'] if q['kind'] == 'all_required_delivery')
        q['scope']['cutoff'] = 2
        self.assertEqual(self.claims(c)['all_required_delivery']['state'], 'INDETERMINATE')
        self.assertEqual(self.result(c)['structural_result'], 'PASS')

    def test_empty_targets_cannot_bypass_observer_binding(self):
        c = self.case()
        r = next(r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] == 'receiver_observation')
        native(r, target_id='ep-a', observer_id='ep-b', target_ids=[])
        self.assertEqual(self.claims(c)['receiver_receipt']['state'], 'INDETERMINATE')

    def test_positive_effect_and_counterexample_do_not_yield_support(self):
        c = self.case('dev-09')
        effect = next(r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] == 'effect')
        q = next(q for q in c['queries'] if q['claim_id'] == 'q-effect-earlier')
        native(effect, operation_id=q['scope']['operation_id'], window=q['scope']['window'])
        claims = {q['claim_id']: q for q in self.result(c)['claims']}
        self.assertEqual(claims['q-effect-earlier']['state'], 'INDETERMINATE')

    def test_ordering_cutoff_and_authority_are_preserved(self):
        c = self.case('dev-09'); q = next(q for q in c['queries'] if q['kind'] == 'ordering')
        q['scope']['cutoff'] = 2
        self.assertEqual(self.claims(c)['ordering']['state'], 'INDETERMINATE')
        q['scope']['cutoff'] = 10
        for r in c['records']:
            if json.loads(r['payload_utf8'])['kind'] == 'enforcement': native(r, observer_id='ep-a-declared')
        result = self.claims(c)['ordering']
        self.assertEqual(result['qualification'], 'CONDITIONALLY_SUPPORTED')
        self.assertEqual(result['conditions'], ['authority_binding_declared_only'])

    def test_semantic_missing_provenance_is_not_refutation(self):
        c = self.case('dev-12')
        r = next(r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] == 'transformation')
        native(r, source_record_id='not-present', state_mapping={s: s for s in self.profile['semantic_state_vocabulary']}, destination_state='UNKNOWN')
        self.assertEqual(self.claims(c)['semantic_preservation']['state'], 'INDETERMINATE')

    def test_semantic_source_authority_preserved(self):
        c = self.case('dev-12')
        r = next(r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] == 'transformation')
        native(r, state_mapping={s: s for s in self.profile['semantic_state_vocabulary']}, destination_state='UNKNOWN')
        source = next(r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] == 'enforcement')
        native(source, observer_id='ep-a-declared')
        self.assertEqual(self.claims(c)['semantic_preservation']['qualification'], 'CONDITIONALLY_SUPPORTED')

    def test_contradictory_receipt_is_not_supported(self):
        c = self.case(); r = copy.deepcopy(next(r for r in c['records'] if json.loads(r['payload_utf8'])['kind'] == 'receiver_observation'))
        r['record_id'] = 'contradiction'; native(r, outcome='NOT_RECEIVED'); c['records'].append(r)
        self.assertEqual(self.claims(c)['receiver_receipt']['state'], 'INDETERMINATE')
        self.assertEqual(self.result(c)['obligation_counts']['CONFLICT'], 1)

    def test_effect_boundary_and_method_are_not_substituted(self):
        c = self.case('dev-09'); q = next(q for q in c['queries'] if q['claim_id'] == 'q-effect-later')
        for key, value in [('boundary_id', 'provider-entry'), ('method', 'different-method')]:
            changed = copy.deepcopy(c)
            next(q for q in changed['queries'] if q['claim_id'] == 'q-effect-later')['scope'][key] = value
            result = {q['claim_id']: q for q in self.result(changed)['claims']}
            self.assertEqual(result['q-effect-later']['state'], 'INDETERMINATE')

    def test_duplicate_envelope_identity_is_rejected(self):
        c = self.case(); c['records'].append(copy.deepcopy(c['records'][0]))
        for baseline in self.profile['baseline_contracts']:
            with self.assertRaises(ValueError): self.result(c, baseline)

    def test_output_mount_rejects_preexisting_data(self):
        import tempfile
        from isolated_run import run
        with tempfile.TemporaryDirectory() as td:
            output = Path(td); (output / 'unapproved-data.json').write_text('{}')
            with self.assertRaises(FileExistsError): run(PACKAGE, 'development', output)


if __name__ == '__main__':
    unittest.main()
