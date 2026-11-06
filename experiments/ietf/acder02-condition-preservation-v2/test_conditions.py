import copy
import itertools
import json
import unittest
from evaluate import FROZEN, evaluate, frozen


def case(name):
    split = 'holdout' if name.startswith('holdout') else 'development'
    return json.loads((FROZEN / 'scenarios' / split / name / 'evidence.json').read_text())


def change(c, record_id, **changes):
    r = next(r for r in c['records'] if r['record_id'] == record_id)
    p = json.loads(r['payload_utf8'])
    p.update(changes)
    r['payload_utf8'] = json.dumps(p, sort_keys=True, separators=(',', ':'))
    r['payload_sha256'] = frozen.digest(r['payload_utf8'])


PROFILE = json.loads((FROZEN / 'PROFILE.json').read_text())


def claims(c):
    return {r['claim_id']: r for r in evaluate(c, PROFILE)['claims']}


def delivery_case():
    c = case('dev-08')
    c['queries'].append({'claim_id': 'mutation-all', 'kind': 'all_required_delivery',
                         'subject': {'instruction_ids': c['population']['manifest_instruction_ids']},
                         'scope': {'clock_id': 'mono', 'cutoff': 10}})
    return c


class Conditions(unittest.TestCase):
    def test_known_missing_receiver_and_obligation_remain_distinct(self):
        result = evaluate(case('holdout-05'), PROFILE)
        row = next(r for r in result['claims'] if r['claim_id'] == 'q-all')
        self.assertEqual(row['conditions'], ['missing_receiver_observation', 'other_target_observation'])
        self.assertEqual(row['state'], 'INDETERMINATE')
        self.assertTrue(any(o['disposition'] == 'UNCONFIRMED' for o in result['obligations']))

    def test_known_refusal_keeps_both_causes_and_references(self):
        row = claims(case('holdout-12'))['q-enforcement']
        self.assertEqual(row['state'], 'REFUTED')
        self.assertEqual(row['conditions'], ['semantic_mapping_not_lossless',
                                             'source_state_does_not_establish_applied'])
        self.assertIn('record:r-transform', row['evidence_refs'])
        self.assertIn('record:r-enforcement', row['evidence_refs'])

    def test_native_outcomes_crossed_with_mapping_loss(self):
        for outcome, lossy in itertools.product(['APPLIED', 'REFUSED', 'NO_EFFECT', 'UNKNOWN'], [False, True]):
            with self.subTest(outcome=outcome, lossy=lossy):
                c = case('holdout-12')
                change(c, 'r-enforcement', outcome=outcome)
                mapping = {s: s for s in PROFILE['semantic_state_vocabulary']}
                if lossy:
                    mapping['UNKNOWN'] = 'APPLIED'
                change(c, 'r-transform', source_state=outcome, destination_state=outcome, state_mapping=mapping)
                row = claims(c)['q-enforcement']
                self.assertEqual(row['state'], {'APPLIED': 'SUPPORTED', 'REFUSED': 'REFUTED',
                                               'NO_EFFECT': 'REFUTED', 'UNKNOWN': 'INDETERMINATE'}[outcome])
                causes = {d['condition'] for d in row['cause_details']}
                self.assertEqual('semantic_mapping_not_lossless' in causes, lossy)
                if outcome != 'APPLIED':
                    self.assertEqual('semantic_mapping_not_lossless' in row['conditions'], lossy)

    def test_conflicting_positive_negative_keeps_mapping_cause(self):
        c = case('holdout-12')
        extra = copy.deepcopy(next(r for r in c['records'] if r['record_id'] == 'r-enforcement'))
        extra['record_id'] = 'r-positive'
        c['records'].append(extra)
        change(c, 'r-positive', outcome='APPLIED')
        row = claims(c)['q-enforcement']
        self.assertEqual(row['state'], 'INDETERMINATE')
        self.assertIn('semantic_mapping_not_lossless', row['conditions'])
        self.assertIn('CONTRADICTORY_NATIVE_ASSERTIONS', row['reason_codes'])

    def test_unrelated_transform_cannot_supply_cause(self):
        c = case('holdout-12')
        change(c, 'r-transform', source_record_id='unrelated')
        self.assertNotIn('semantic_mapping_not_lossless', claims(c)['q-enforcement']['conditions'])

    def test_invalid_and_substituted_receiver_causes_accumulate(self):
        c = delivery_case()
        change(c, 'r-receiver', content_sha256='0' * 64, boundary_id='wrong')
        row = next(r for r in claims(c).values() if r['kind'] == 'all_required_delivery')
        self.assertTrue({'governed_content_substitution', 'invalid_receiver_record',
                         'missing_receiver_observation'} <= set(row['conditions']))
        self.assertNotEqual(row['state'], 'SUPPORTED')

    def test_other_target_not_mistaken_for_missing_event_globally(self):
        c = delivery_case()
        change(c, 'r-receiver', target_id='ep-b', observer_id='ep-b')
        row = next(r for r in claims(c).values() if r['kind'] == 'all_required_delivery')
        self.assertIn('other_target_observation', row['conditions'])
        self.assertIn('missing_receiver_observation', row['conditions'])
        self.assertIn('record:r-receiver', row['evidence_refs'])

    def test_query_cutoff_uses_v2_cause_collection(self):
        c = delivery_case()
        q = next(q for q in c['queries'] if q['kind'] == 'all_required_delivery')
        q['scope']['cutoff'] = 2
        self.assertIn('missing_receiver_observation', claims(c)[q['claim_id']]['conditions'])

    def test_all_known_claim_states_qualifications_and_accounting_unchanged(self):
        for path in sorted((FROZEN / 'scenarios').rglob('evidence.json')):
            c = json.loads(path.read_text())
            before, after = frozen.evaluate(c, PROFILE, 'acder_bounded'), evaluate(c, PROFILE)
            for old, new in zip(before['claims'], after['claims']):
                with self.subTest(case=c['case_id'], claim=old['claim_id']):
                    for key in ('state', 'qualification', 'scope', 'subject'):
                        self.assertEqual(old[key], new[key])
            for key in ('obligations', 'obligation_counts', 'receiver_record_counts', 'structural_result'):
                self.assertEqual(before[key], after[key])

    def test_label_renaming_and_record_order_do_not_control_decision(self):
        c = case('holdout-12')
        before = claims(c)
        c['case_id'] = 'unknown-label'
        c['records'].reverse()
        self.assertEqual(before, claims(c))


if __name__ == '__main__':
    unittest.main()
