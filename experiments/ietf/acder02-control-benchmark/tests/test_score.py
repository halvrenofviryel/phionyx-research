"""Small invented scorer-contract fixtures; never execute a benchmark comparator."""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
import score


def claim(claim_id, state='SUPPORTED', qualification='FULLY_SUPPORTED', conditions=None):
    return {'claim_id': claim_id, 'state': state, 'qualification': qualification,
            'conditions': conditions or [], 'reason_codes': [], 'evidence_refs': []}


def query(claim_id, state='SUPPORTED', kind='receiver_receipt', truth=True,
          qualification='FULLY_SUPPORTED', conditions=None, ambiguous=False):
    return {'claim_id': claim_id, 'kind': kind, 'subject': {'instruction_id': 'invented-i'},
            'scope': {'target_id': 'invented-target', 'cutoff': 10},
            'oracle': {'justified_state': state, 'qualification': qualification,
                       'conditions': conditions or [], 'ambiguous': ambiguous,
                       'rationale': 'Invented scorer test; no benchmark observation'},
            'latent_truth': truth}


def reconciliation():
    return {'obligations': [{'instruction_id': 'invented-i', 'target_id': 'invented-target', 'disposition': 'CONFIRMED'}],
            'instruction_accounting': {'total': 1, 'with_obligations': 1, 'terminal_empty': 0, 'all_excluded': 0, 'target_resolution_unclosed': 0},
            'obligation_counts': {'total': 1, **{s: int(s == 'CONFIRMED') for s in ('SUBSTITUTION', 'CONFLICT', 'INVALID', 'EXPLICIT_FAILURE', 'INDETERMINATE', 'UNCONFIRMED', 'CONFIRMED')}},
            'receiver_record_counts': {'total': 1, **{s: int(s == 'matched') for s in ('substitution', 'conflict', 'invalid', 'duplicate', 'matched', 'orphan')}},
            'structural_result': 'PASS', 'aggregate_claim': {'qualification': 'FULLY_SUPPORTED', 'conditions': []}}


def case(queries, case_id='invented-case', split='development'):
    return {'case_id': case_id, 'split': split, 'category_id': 'invented-category',
            'queries': queries, 'reconciliation': reconciliation()}


def output(queries, case_id='invented-case'):
    return {'case_id': case_id, 'claims': queries, **reconciliation()}


def group(report, comparator='acder_bounded', split='total', kind='ALL_KINDS'):
    return next(g for g in report['metrics'] if (g['comparator'], g['split'], g['kind']) == (comparator, split, kind))


class MetricTests(unittest.TestCase):
    def test_frozen_numerators_distinguish_epistemic_and_latent_errors(self):
        oracle_states = ['INDETERMINATE', 'INDETERMINATE', 'SUPPORTED', 'SUPPORTED', 'SUPPORTED', 'INDETERMINATE', 'REFUTED']
        predicted_states = ['SUPPORTED', 'SUPPORTED', 'REFUTED', 'INDETERMINATE', 'SUPPORTED', 'INDETERMINATE', 'REFUTED']
        truths = [True, False, True, True, True, False, False]
        queries, claims = [], []
        for i, (expected, predicted, truth) in enumerate(zip(oracle_states, predicted_states, truths)):
            queries.append(query(str(i), expected, truth=truth, qualification='FULLY_SUPPORTED' if expected == 'SUPPORTED' else 'NOT_SUPPORTED'))
            claims.append(claim(str(i), predicted, 'FULLY_SUPPORTED' if predicted == 'SUPPORTED' else 'NOT_SUPPORTED'))
        report = score.score([case(queries)], {'acder_bounded': [output(claims)]})
        actual = group(report)
        expected = {'unsupported_stronger_support': (2, 4), 'semantic_incorrectness': (2, 5),
                    'false_rejection': (1, 3), 'useful_support_recall': (1, 3),
                    'appropriate_withholding': (1, 3), 'state_agreement': (3, 7),
                    'qualification_agreement': (3, 7), 'exact_condition_retention': (7, 7)}
        for name, (num, den) in expected.items():
            self.assertEqual(actual['metrics'][name], {'numerator': num, 'denominator': den, 'rate': num/den})
        self.assertEqual(actual['counts']['unsupported_but_latently_true_assertions'], 1)
        self.assertEqual(actual['counts']['oracle_supported_withheld_indeterminate'], 1)
        self.assertEqual(actual['state_confusion']['SUPPORTED']['REFUTED'], 1)
        self.assertEqual(sum(sum(row.values()) for row in actual['state_confusion'].values()), 7)
        self.assertEqual(set(actual['state_confusion']), set(score.STATES))
        self.assertTrue(all(set(row) == set(score.STATES) for row in actual['state_confusion'].values()))
        self.assertFalse(report['all_rows'][0]['semantic_incorrect'])
        self.assertTrue(report['all_rows'][1]['semantic_incorrect'])
        self.assertTrue(report['all_rows'][0]['unsupported_but_latently_true'])
        self.assertFalse(report['all_rows'][1]['unsupported_but_latently_true'])

    def test_fixed_applicability_prevents_na_denominator_escape(self):
        report = score.score([case([query('q')])], {'naive_ack': [output([claim('q', 'NOT_APPLICABLE', None)])]})
        bucket = group(report, 'naive_ack')
        self.assertEqual(bucket['metrics']['useful_support_recall'], score.metric(0, 1))
        self.assertEqual(bucket['metrics']['state_agreement'], score.metric(0, 1))
        self.assertEqual(bucket['state_confusion']['SUPPORTED']['NOT_APPLICABLE'], 1)
        self.assertEqual(bucket['counts']['unexpected_not_applicable_primary'], 1)

    def test_fixed_nonapplicability_and_integrity_are_distinct(self):
        queries = [query('integrity', 'REFUTED', kind='envelope_integrity', truth=False, qualification='NOT_SUPPORTED'), query('delivery')]
        report = score.score([case(queries)], {'integrity_only': [output([claim('integrity'), claim('delivery')])]})
        bucket = group(report, 'integrity_only')
        self.assertEqual(bucket['counts']['contract_applicable'], 1)
        self.assertEqual(bucket['counts']['outside_contract_non_na_output'], 1)
        self.assertEqual(bucket['metrics']['unsupported_stronger_support'], score.metric(0, 0))
        self.assertEqual(bucket['metrics']['semantic_incorrectness'], score.metric(1, 1))
        self.assertEqual(group(report, 'integrity_only', kind='receiver_receipt')['metrics']['state_agreement'], score.metric(0, 0))

    def test_ambiguity_excludes_only_one_claim_not_structural_case(self):
        evidence = case([query('ambiguous', ambiguous=True), query('clear')])
        predicted = output([claim('ambiguous', 'REFUTED', 'NOT_SUPPORTED'), claim('clear')])
        predicted['structural_result'] = 'FAIL'
        report = score.score([evidence], {'acder_bounded': [predicted]})
        self.assertEqual(group(report)['metrics']['state_agreement'], score.metric(1, 1))
        self.assertEqual(group(report)['counts']['ambiguous_applicable_excluded'], 1)
        self.assertEqual(len(report['all_rows']), 2)
        self.assertEqual(report['structural_summary'][-1]['field_mismatches']['structural_result'], 1)

    def test_qualification_and_conditions_scored_independently(self):
        expected = query('q', 'INDETERMINATE', qualification='CONDITIONALLY_SUPPORTED', conditions=['coverage_declared_only'])
        predicted = claim('q', 'INDETERMINATE', 'NOT_SUPPORTED')
        report = score.score([case([expected])], {'acder_bounded': [output([predicted])]})
        metrics = group(report)['metrics']
        self.assertEqual(metrics['state_agreement'], score.metric(1, 1))
        self.assertEqual(metrics['qualification_agreement'], score.metric(0, 1))
        self.assertEqual(metrics['exact_condition_retention'], score.metric(0, 1))
        self.assertEqual(report['all_rows'][0]['missing_conditions'], ['coverage_declared_only'])

    def test_condition_order_is_not_a_difference(self):
        conditions = ['coverage_declared_only', 'authority_binding_declared_only']
        report = score.score([case([query('q', conditions=conditions)])], {'acder_bounded': [output([claim('q', conditions=conditions[::-1])])]})
        self.assertEqual(group(report)['metrics']['exact_condition_retention'], score.metric(1, 1))

    def test_no_truth_is_not_false_and_unknown_is_not_semantic_error(self):
        queries = [query('null', truth=None), query('unknown', truth=False)]
        report = score.score([case(queries)], {'acder_bounded': [output([claim('null'), claim('unknown', 'NOT_EVALUATED', None)])]})
        self.assertEqual(group(report)['metrics']['semantic_incorrectness'], score.metric(0, 0))
        self.assertEqual(group(report)['counts']['definite_predictions_without_latent_bool'], 1)
        self.assertEqual(group(report)['counts']['oracle_supported_withheld_not_evaluated'], 1)
        self.assertTrue(all(r['semantic_incorrect'] is None for r in report['all_rows']))

    def test_split_kind_and_total_partitions(self):
        cases = [case([query('d')]), case([query('h', kind='enforcement_applied')], 'other', 'holdout')]
        predictions = {'acder_bounded': [output([claim('d')]), output([claim('h')], 'other')]}
        report = score.score(cases, predictions)
        self.assertEqual(group(report, split='development')['counts']['primary_eligible'], 1)
        self.assertEqual(group(report, split='holdout')['counts']['primary_eligible'], 1)
        self.assertEqual(group(report)['counts']['primary_eligible'], 2)
        self.assertEqual(group(report, split='holdout', kind='receiver_receipt')['metrics']['state_agreement']['rate'], None)
        self.assertEqual(group(report, split='holdout', kind='enforcement_applied')['metrics']['state_agreement'], score.metric(1, 1))

    def test_aggregate_prose_unscored_and_counts_type_sensitive(self):
        evidence = case([query('q')])
        predicted = output([claim('q')])
        predicted['aggregate_claim'].update(fact='Different display prose', scope={'display': 'retained'})
        predicted['receiver_record_counts']['orphan'] = False
        report = score.score([evidence], {'acder_bounded': [predicted]})
        comparison = report['structural_comparisons'][0]
        self.assertTrue(comparison['comparisons']['aggregate_claim']['equal'])
        self.assertFalse(comparison['comparisons']['receiver_record_counts']['equal'])
        self.assertEqual(group(report)['metrics']['state_agreement'], score.metric(1, 1))
        self.assertEqual(comparison['predicted_reconciliation']['aggregate_claim']['fact'], 'Different display prose')

    def test_structural_missing_fields_and_wrong_target_remain_visible(self):
        predicted = output([claim('q')])
        del predicted['instruction_accounting']
        predicted['obligations'][0]['target_id'] = 'other-target'
        report = score.score([case([query('q')])], {'acder_bounded': [predicted]})
        checks = report['structural_comparisons'][0]['comparisons']
        self.assertEqual(checks['instruction_accounting']['differences'][0]['issue'], 'missing')
        self.assertEqual(checks['obligations']['differences'][0]['path'], '$.obligations[0].target_id')

    def test_input_objects_are_not_mutated(self):
        cases, predictions = [case([query('q')])], {'acder_bounded': [output([claim('q')])]}
        snapshot = copy.deepcopy((cases, predictions))
        score.score(cases, predictions)
        self.assertEqual((cases, predictions), snapshot)

    def test_missing_duplicate_unknown_and_malformed_claims_fail_closed(self):
        original = {'acder_bounded': [output([claim('q')])]}
        mutations = [lambda p: p['acder_bounded'].clear(),
                     lambda p: p['acder_bounded'][0]['claims'].clear(),
                     lambda p: p['acder_bounded'][0]['claims'].append(claim('q')),
                     lambda p: p['acder_bounded'][0]['claims'][0].update(state='PASS'),
                     lambda p: p['acder_bounded'][0]['claims'][0].update(conditions=['made-up']),
                     lambda p: p['acder_bounded'][0]['claims'][0].update(conditions=['coverage_declared_only']*2),
                     lambda p: p.update(unregistered=[])]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                predictions = copy.deepcopy(original); mutate(predictions)
                with self.assertRaises(score.InputError):
                    score.score([case([query('q')])], predictions)

    def test_ambiguity_and_latent_types_are_explicit(self):
        for key, value in [('latent_truth', 0), ('latent_truth', 'false')]:
            q = query('q'); q[key] = value
            with self.assertRaises(score.InputError):
                score.score([case([q])], {'naive_ack': [output([claim('q')])]})
        q = query('q'); del q['oracle']['ambiguous']
        with self.assertRaises(score.InputError):
            score.score([case([q])], {'naive_ack': [output([claim('q')])]})

    def test_subset_of_comparators_is_explicitly_incomplete(self):
        report = score.score([case([query('q')])], {'naive_ack': [output([claim('q')])]})
        self.assertFalse(report['complete_three_comparator_run'])
        self.assertEqual(report['missing_comparators'], ['acder_bounded', 'integrity_only'])


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-k1-score-tests-')
        self.root = pathlib.Path(self.temp.name)
        self.evidence = self.root/'evidence/development'
        self.oracles = self.root/'oracle/development'
        q = query('invented-row')
        evidence = {'schema': 'acder02-control-benchmark-evidence-v1', 'case_id': 'dev-01',
                    'profile_id': 'acder02-control-benchmark-v1', 'population': {}, 'instructions': [], 'records': [],
                    'queries': [{k: v for k, v in q.items() if k not in ('oracle', 'latent_truth')}]}
        oracle = {'schema': 'acder02-control-benchmark-oracle-v1', 'case_id': 'dev-01', 'derivation': 'invented unit fixture',
                  'claims': [{'claim_id': q['claim_id'], 'kind': q['kind'], **q['oracle'],
                              'latent_truth_ref': 'latent_truth.json#/claim_truth/invented-row'}], 'reconciliation': reconciliation()}
        latent = {'schema': 'acder02-synthetic-latent-truth-v1', 'case_id': 'dev-01', 'status': 'invented',
                  'claim_truth': {'invented-row': True}, 'latent_facts': []}
        for path, value in [(self.evidence/'dev-01/evidence.json', evidence), (self.oracles/'dev-01/oracle.json', oracle),
                            (self.oracles/'dev-01/latent_truth.json', latent)]:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
        self.predictions = self.root/'predictions.json'
        self.predictions.write_text(json.dumps({'naive_ack': [output([claim('invented-row')], 'dev-01')]}))
        self.result = self.root/'score.json'

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self):
        return subprocess.run([sys.executable, '-B', str(pathlib.Path(score.__file__)), '--evidence-dir', str(self.evidence),
                               '--oracle-dir', str(self.oracles), '--predictions', str(self.predictions), '--out', str(self.result)],
                              capture_output=True, text=True)

    def test_actual_subprocess_loader_and_first_result_preservation(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = self.result.read_bytes()
        report = json.loads(saved)
        self.assertEqual(report['all_rows'][0]['category_id'], 'cat-01')
        self.assertEqual(report['all_rows'][0]['oracle']['rationale'], 'Invented scorer test; no benchmark observation')
        self.assertEqual(report['all_rows'][0]['input_files']['evidence']['path'], str(self.evidence/'dev-01/evidence.json'))
        repeated = self.run_cli()
        self.assertEqual(repeated.returncode, 2)
        self.assertIn('output already exists', repeated.stderr)
        self.assertEqual(self.result.read_bytes(), saved)

    def test_loader_does_not_open_neighbor_subtree(self):
        forbidden = self.root/'evidence/withheld-neighbor/sentinel/evidence.json'
        forbidden.parent.mkdir(parents=True); forbidden.write_text('DO NOT PARSE')
        cases = score.load_cases(self.evidence, self.oracles)
        self.assertEqual([c['case_id'] for c in cases], ['dev-01'])

    def test_missing_claim_fails_without_output_artifact(self):
        self.predictions.write_text(json.dumps({'naive_ack': [output([], 'dev-01')]}))
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn('missing or unknown claim', result.stderr)
        self.assertFalse(self.result.exists())

    def test_loader_refuses_case_identity_or_claim_inventory_mismatch(self):
        latent_path = self.oracles/'dev-01/latent_truth.json'
        latent = json.loads(latent_path.read_text()); latent['case_id'] = 'other'
        latent_path.write_text(json.dumps(latent))
        with self.assertRaises(score.InputError):
            score.load_cases(self.evidence, self.oracles)

    def test_duplicate_json_keys_rejected(self):
        self.predictions.write_text('{"naive_ack": [], "naive_ack": []}')
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn('duplicate JSON key', result.stderr)
        self.assertFalse(self.result.exists())

    def test_non_object_author_file_is_an_input_error(self):
        (self.oracles/'dev-01/oracle.json').write_text('null')
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn('must contain objects', result.stderr)
        self.assertFalse(self.result.exists())


if __name__ == '__main__':
    unittest.main()
