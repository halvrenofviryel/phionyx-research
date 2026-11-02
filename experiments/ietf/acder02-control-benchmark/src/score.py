#!/usr/bin/env python3
"""Frozen-metric K1 scorer. No comparator execution or oracle derivation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys

STATES = ('SUPPORTED', 'REFUTED', 'INDETERMINATE', 'NOT_EVALUATED', 'NOT_APPLICABLE')
QUALIFICATIONS = ('FULLY_SUPPORTED', 'CONDITIONALLY_SUPPORTED', 'NOT_SUPPORTED', None)
PROFILE_SHA256 = '8c27cd685289028261ff5c035a6d9643c58412954bff8ebee7ffaa485c9e8a54'
PROFILE_PATH = pathlib.Path(__file__).resolve().parent.parent/'PROFILE.json'
SELECTION_SHA256 = '8cf277d7d7edf246a497394ef33c01ac32a98735d9402bbb6602c51add948b7b'
METRICS = ('unsupported_stronger_support', 'semantic_incorrectness', 'false_rejection',
           'useful_support_recall', 'appropriate_withholding', 'state_agreement',
           'qualification_agreement', 'exact_condition_retention')
RECON_FIELDS = ('obligations', 'instruction_accounting', 'obligation_counts',
                'receiver_record_counts', 'structural_result', 'aggregate_claim')


class InputError(ValueError):
    """Malformed/incomplete scoring input; never silently repair or drop a row."""


def require(condition, message):
    if not condition:
        raise InputError(message)


def load_json(path):
    def unique_pairs(pairs):
        value = {}
        for key, child in pairs:
            require(key not in value, f'duplicate JSON key: {key}')
            value[key] = child
        return value
    def invalid_constant(value):
        raise InputError(f'non-finite JSON number: {value}')
    return json.loads(pathlib.Path(path).read_bytes(), object_pairs_hook=unique_pairs,
                      parse_constant=invalid_constant)


def profile():
    require(hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest() == PROFILE_SHA256,
            'shared PROFILE.json differs from preregistered scoring contract')
    return load_json(PROFILE_PATH)


def unique_index(rows, field, location):
    require(type(rows) is list, f'{location}: expected array')
    result = {}
    for row in rows:
        require(type(row) is dict and type(row.get(field)) is str and row[field],
                f'{location}: missing/non-string {field}')
        require(row[field] not in result, f'{location}: duplicate {field} {row[field]}')
        result[row[field]] = row
    return result


def check_claim(claim, location, conditions, oracle=False):
    require(type(claim) is dict, f'{location}: expected object')
    state_field = 'justified_state' if oracle else 'state'
    require(claim.get(state_field) in STATES, f'{location}: invalid/missing {state_field}')
    require('qualification' in claim and claim['qualification'] in QUALIFICATIONS,
            f'{location}: invalid/missing qualification')
    values = claim.get('conditions')
    require(type(values) is list and all(type(v) is str and v in conditions for v in values),
            f'{location}: invalid/missing condition vocabulary')
    require(len(values) == len(set(values)), f'{location}: duplicate conditions')
    if oracle:
        require(type(claim.get('ambiguous')) is bool, f'{location}: explicit ambiguity bool required')
    else:
        for field in ('reason_codes', 'evidence_refs'):
            require(type(claim.get(field)) is list and all(type(v) is str for v in claim[field]),
                    f'{location}: invalid/missing {field}')


def typed_equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(typed_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def differences(expected, predicted, path='$'):
    """Type-sensitive comparison; absent is different from JSON null."""
    if typed_equal(expected, predicted):
        return []
    if type(expected) is dict and type(predicted) is dict:
        result = []
        for key in sorted(expected.keys() | predicted.keys()):
            next_path = path + '.' + key
            if key not in expected:
                result.append({'path': next_path, 'issue': 'unexpected', 'predicted': predicted[key]})
            elif key not in predicted:
                result.append({'path': next_path, 'issue': 'missing', 'expected': expected[key]})
            else:
                result.extend(differences(expected[key], predicted[key], next_path))
        return result
    if type(expected) is list and type(predicted) is list:
        result = []
        for i in range(max(len(expected), len(predicted))):
            next_path = f'{path}[{i}]'
            if i >= len(expected):
                result.append({'path': next_path, 'issue': 'unexpected', 'predicted': predicted[i]})
            elif i >= len(predicted):
                result.append({'path': next_path, 'issue': 'missing', 'expected': expected[i]})
            else:
                result.extend(differences(expected[i], predicted[i], next_path))
        return result
    return [{'path': path, 'issue': 'value_or_type_mismatch', 'expected': expected, 'predicted': predicted}]


def structural_comparison(case, prediction, comparator):
    meta = {key: copy.deepcopy(case[key]) for key in ('case_id', 'split', 'category_id')}
    meta['comparator'] = comparator
    if comparator != 'acder_bounded':
        return {**meta, 'applicable': False, 'reason': 'No reconciliation output in fixed baseline contract'}
    expected = case.get('reconciliation')
    require(type(expected) is dict and all(f in expected for f in RECON_FIELDS),
            f"{case['case_id']}: complete oracle reconciliation required")
    comparisons = {}
    for field in RECON_FIELDS:
        if field not in prediction:
            comparisons[field] = {'equal': False, 'differences': [
                {'path': '$.' + field, 'issue': 'missing', 'expected': expected[field]}]}
        elif field == 'aggregate_claim' and type(prediction[field]) is dict:
            scored_expected = {k: expected[field][k] for k in ('qualification', 'conditions')}
            scored_prediction = {k: prediction[field][k] for k in ('qualification', 'conditions') if k in prediction[field]}
            # Prose and fact/scope remain inspectable. They are not exact-string labels.
            for value in (scored_expected, scored_prediction):
                if type(value.get('conditions')) is list and all(type(c) is str for c in value['conditions']):
                    value['conditions'] = sorted(set(value['conditions']))
            delta = differences(scored_expected, scored_prediction, '$.' + field)
            original_conditions = prediction[field].get('conditions')
            if type(original_conditions) is list and all(type(c) is str for c in original_conditions) and len(original_conditions) != len(set(original_conditions)):
                delta.append({'path': '$.aggregate_claim.conditions', 'issue': 'duplicate_conditions', 'predicted': original_conditions})
            comparisons[field] = {'equal': not delta, 'differences': delta}
        else:
            delta = differences(expected[field], prediction[field], '$.' + field)
            comparisons[field] = {'equal': not delta, 'differences': delta}
    aggregate_delta = comparisons['aggregate_claim']['differences']
    return {**meta, 'applicable': True, 'all_equal': all(c['equal'] for c in comparisons.values()),
            'aggregate_qualification_equal': not any(d['path'] in ('$.aggregate_claim', '$.aggregate_claim.qualification') for d in aggregate_delta),
            'aggregate_conditions_equal': not any(d['path'] == '$.aggregate_claim' or d['path'].startswith('$.aggregate_claim.conditions') for d in aggregate_delta),
            'comparisons': comparisons,
            'oracle_reconciliation': copy.deepcopy(expected),
            'predicted_reconciliation': {f: copy.deepcopy(prediction[f]) for f in RECON_FIELDS if f in prediction}}


def load_cases(evidence_dir, oracle_dir):
    """Load only the explicitly supplied evidence subtree; no implicit split discovery."""
    evidence_dir, oracle_dir = pathlib.Path(evidence_dir), pathlib.Path(oracle_dir)
    selection_path = PROFILE_PATH.with_name('SCENARIO_SELECTION.json')
    require(hashlib.sha256(selection_path.read_bytes()).hexdigest() == SELECTION_SHA256,
            'SCENARIO_SELECTION.json differs from preregistered contract')
    selection = load_json(selection_path)
    labels = {}
    for category in selection['categories']:
        for split, key in [('development', 'development_case_id'), ('holdout', 'holdout_case_id')]:
            require(category[key] not in labels, 'duplicate selected case ID')
            labels[category[key]] = (split, category['category_id'], category['name'])
    cases = []
    for evidence_path in sorted(evidence_dir.rglob('evidence.json')):
        relative = evidence_path.parent.relative_to(evidence_dir)
        oracle_path = oracle_dir/relative/'oracle.json'
        latent_path = oracle_dir/relative/'latent_truth.json'
        evidence, oracle, latent = (load_json(p) for p in (evidence_path, oracle_path, latent_path))
        require(all(type(value) is dict for value in (evidence, oracle, latent)), 'evidence/oracle/latent files must contain objects')
        require(evidence.get('schema') == 'acder02-control-benchmark-evidence-v1', 'unexpected evidence schema')
        require(evidence.get('profile_id') == 'acder02-control-benchmark-v1', 'unexpected evidence profile')
        require(oracle.get('schema') == 'acder02-control-benchmark-oracle-v1', 'unexpected oracle schema')
        require(latent.get('schema') == 'acder02-synthetic-latent-truth-v1', 'unexpected latent truth schema')
        cid = evidence.get('case_id')
        require(cid in labels, f'case not in frozen selection: {cid}')
        require(oracle.get('case_id') == latent.get('case_id') == cid, f'{cid}: evidence/oracle/latent case mismatch')
        queries = unique_index(evidence.get('queries'), 'claim_id', f'{cid}.evidence.queries')
        expected = unique_index(oracle.get('claims'), 'claim_id', f'{cid}.oracle.claims')
        truth = latent.get('claim_truth')
        require(type(truth) is dict and queries.keys() == expected.keys() == truth.keys(),
                f'{cid}: evidence/oracle/latent claim inventory mismatch')
        normalized = []
        for claim_id, query in queries.items():
            require(expected[claim_id].get('kind') == query['kind'], f'{cid}.{claim_id}: oracle kind mismatch')
            require(expected[claim_id].get('latent_truth_ref') == f'latent_truth.json#/claim_truth/{claim_id}',
                    f'{cid}.{claim_id}: latent truth reference mismatch')
            normalized.append({**copy.deepcopy(query), 'oracle': copy.deepcopy(expected[claim_id]),
                               'latent_truth': truth[claim_id]})
        split, category_id, category_name = labels[cid]
        cases.append({'case_id': cid, 'split': split, 'category_id': category_id,
                      'category_name': category_name, 'queries': normalized,
                      'reconciliation': copy.deepcopy(oracle.get('reconciliation')),
                      'oracle_derivation': copy.deepcopy(oracle.get('derivation')),
                      'latent_world': {k: copy.deepcopy(v) for k, v in latent.items() if k != 'claim_truth'},
                      'input_files': {name: {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                                      for name, path in [('evidence', evidence_path), ('oracle', oracle_path), ('latent_truth', latent_path)]}})
    require(cases, 'no evidence.json found in explicitly supplied evidence directory')
    return cases


def metric(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator,
            'rate': numerator/denominator if denominator else None}


def bucket(rows):
    eligible = [r for r in rows if r['primary_eligible']]
    unsupported = [r for r in eligible if r['kind'] != 'envelope_integrity' and r['oracle']['justified_state'] != 'SUPPORTED']
    supportable = [r for r in eligible if r['oracle']['justified_state'] == 'SUPPORTED']
    unknown = [r for r in eligible if r['oracle']['justified_state'] in ('INDETERMINATE', 'NOT_EVALUATED')]
    definite = [r for r in eligible if r['semantic_comparable']]
    predicted = lambda r: r['prediction']['state']
    confusion = {oracle: {prediction: 0 for prediction in STATES} for oracle in STATES}
    for row in eligible:
        confusion[row['oracle']['justified_state']][predicted(row)] += 1
    metrics = {
        'unsupported_stronger_support': metric(sum(predicted(r) == 'SUPPORTED' for r in unsupported), len(unsupported)),
        'semantic_incorrectness': metric(sum(r['semantic_incorrect'] for r in definite), len(definite)),
        'false_rejection': metric(sum(predicted(r) == 'REFUTED' for r in supportable), len(supportable)),
        'useful_support_recall': metric(sum(predicted(r) == 'SUPPORTED' for r in supportable), len(supportable)),
        'appropriate_withholding': metric(sum(predicted(r) in ('INDETERMINATE', 'NOT_EVALUATED') for r in unknown), len(unknown)),
        'state_agreement': metric(sum(r['state_equal'] for r in eligible), len(eligible)),
        'qualification_agreement': metric(sum(r['qualification_equal'] for r in eligible), len(eligible)),
        'exact_condition_retention': metric(sum(r['conditions_equal'] for r in eligible), len(eligible)),
    }
    return {'counts': {
        'all_rows': len(rows), 'contract_applicable': sum(r['applicable'] for r in rows),
        'contract_not_applicable': sum(not r['applicable'] for r in rows),
        'ambiguous_all_rows': sum(r['ambiguous'] for r in rows),
        'ambiguous_applicable_excluded': sum(r['applicable'] and r['ambiguous'] for r in rows),
        'primary_eligible': len(eligible),
        'unexpected_not_applicable_all_rows': sum(r['unexpected_not_applicable'] for r in rows),
        'unexpected_not_applicable_primary': sum(r['unexpected_not_applicable'] for r in eligible),
        'outside_contract_non_na_output': sum(r['outside_contract_non_na_output'] for r in rows),
        'unsupported_but_latently_true_assertions': sum(predicted(r) == 'SUPPORTED' and r['latent_truth'] is True for r in unsupported),
        'oracle_supported_withheld_indeterminate': sum(predicted(r) == 'INDETERMINATE' for r in supportable),
        'oracle_supported_withheld_not_evaluated': sum(predicted(r) == 'NOT_EVALUATED' for r in supportable),
        'predicted_states_all_rows': {s: sum(predicted(r) == s for r in rows) for s in STATES},
        'predicted_states_primary': {s: sum(predicted(r) == s for r in eligible) for s in STATES},
        'oracle_states_primary': {s: sum(r['oracle']['justified_state'] == s for r in eligible) for s in STATES},
        'definite_predictions_without_latent_bool': sum(predicted(r) in ('SUPPORTED', 'REFUTED') and r['latent_truth'] is None for r in eligible),
    }, 'metrics': metrics, 'state_confusion': confusion}


def score(cases, predictions):
    """Score normalized case bundles without mutation; see CONTRACT.md for API."""
    fixed = profile()
    contracts = fixed['baseline_contracts']
    case_index = unique_index(cases, 'case_id', 'cases')
    require(case_index, 'at least one case required')
    require(type(predictions) is dict and predictions, 'predictions must map comparator names to case arrays')
    require(set(predictions) <= set(contracts), 'unknown comparator name')
    for case in cases:
        cid = case['case_id']
        require(case.get('split') in ('development', 'holdout'), f'{cid}: split must be development or holdout')
        require(type(case.get('category_id')) is str, f'{cid}: category_id required')
        query_index = unique_index(case.get('queries'), 'claim_id', f'{cid}.queries')
        require(query_index, f'{cid}: at least one query required')
        for query in query_index.values():
            location = f"{cid}.{query['claim_id']}"
            require(query.get('kind') in fixed['claim_definitions'], f'{location}: unknown query kind')
            require(type(query.get('scope')) is dict and type(query.get('subject')) is dict, f'{location}: explicit scope and subject required')
            check_claim(query.get('oracle'), location + '.oracle', fixed['conditions'], oracle=True)
            require('latent_truth' in query and (query['latent_truth'] is None or type(query['latent_truth']) is bool),
                    f'{location}: latent_truth must be explicit bool or null')
    all_rows, structural = [], []
    for comparator in sorted(predictions):
        outputs = unique_index(predictions[comparator], 'case_id', comparator)
        require(outputs.keys() == case_index.keys(), f'{comparator}: missing or unknown case outputs')
        for cid, case in case_index.items():
            output = outputs[cid]
            claims = unique_index(output.get('claims'), 'claim_id', f'{comparator}.{cid}.claims')
            require(set(claims) == {q['claim_id'] for q in case['queries']}, f'{comparator}.{cid}: missing or unknown claim outputs')
            for query in case['queries']:
                prediction = claims[query['claim_id']]
                check_claim(prediction, f"{comparator}.{cid}.{query['claim_id']}", fixed['conditions'])
                oracle = query['oracle']
                applicable = query['kind'] in contracts[comparator]['applicable_kinds']
                definite = prediction['state'] in ('SUPPORTED', 'REFUTED') and type(query['latent_truth']) is bool
                semantic_error = (prediction['state'] == 'SUPPORTED') != query['latent_truth'] if definite else None
                overclaim = query['kind'] != 'envelope_integrity' and prediction['state'] == 'SUPPORTED' and oracle['justified_state'] != 'SUPPORTED'
                row = {key: copy.deepcopy(value) for key, value in case.items() if key not in ('queries', 'reconciliation')}
                row.update(copy.deepcopy(query))
                row.update({'comparator': comparator, 'prediction': copy.deepcopy(prediction),
                            'applicable': applicable, 'applicability_basis': 'Fixed PROFILE baseline_contracts, independent of output',
                            'ambiguous': oracle['ambiguous'], 'primary_eligible': applicable and not oracle['ambiguous'],
                            'unexpected_not_applicable': applicable and prediction['state'] == 'NOT_APPLICABLE',
                            'outside_contract_non_na_output': not applicable and prediction['state'] != 'NOT_APPLICABLE',
                            'state_equal': oracle['justified_state'] == prediction['state'],
                            'qualification_equal': oracle['qualification'] == prediction['qualification'],
                            'conditions_equal': sorted(oracle['conditions']) == sorted(prediction['conditions']),
                            'missing_conditions': sorted(set(oracle['conditions']) - set(prediction['conditions'])),
                            'extra_conditions': sorted(set(prediction['conditions']) - set(oracle['conditions'])),
                            'semantic_comparable': definite, 'semantic_incorrect': semantic_error})
                row.update({'unsupported_stronger_assertion': overclaim,
                            'unsupported_but_latently_true': overclaim and query['latent_truth'] is True})
                all_rows.append(row)
            structural.append(structural_comparison(case, output, comparator))
    aggregates = []
    for comparator in sorted(predictions):
        for split in ('development', 'holdout', 'total'):
            for kind in (*sorted(fixed['claim_definitions']), 'ALL_KINDS'):
                subset = [r for r in all_rows if r['comparator'] == comparator and
                          (split == 'total' or r['split'] == split) and (kind == 'ALL_KINDS' or r['kind'] == kind)]
                aggregates.append({'comparator': comparator, 'split': split, 'kind': kind, **bucket(subset)})
    structural_summary = []
    for split in ('development', 'holdout', 'total'):
        selected = [r for r in structural if r['applicable'] and (split == 'total' or r['split'] == split)]
        structural_summary.append({'comparator': 'acder_bounded', 'split': split, 'cases': len(selected),
            'exact_case_matches': sum(r['all_equal'] for r in selected),
            'aggregate_qualification_agreement': metric(sum(r['aggregate_qualification_equal'] for r in selected), len(selected)),
            'aggregate_condition_retention': metric(sum(r['aggregate_conditions_equal'] for r in selected), len(selected)),
            'field_mismatches': {f: sum(not r['comparisons'][f]['equal'] for r in selected) for f in RECON_FIELDS}})
    return {'schema': 'k1-frozen-metric-score-v1', 'profile_sha256': PROFILE_SHA256,
            'scope': 'Evidence-oracle and latent synthetic truth scoring only; no automatic oracle correction',
            'case_count': len(cases), 'supplied_comparators': sorted(predictions),
            'missing_comparators': sorted(set(contracts) - set(predictions)),
            'complete_three_comparator_run': set(predictions) == set(contracts),
            'state_order': list(STATES), 'metrics': aggregates, 'all_rows': all_rows,
            'structural_comparisons': structural, 'structural_summary': structural_summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=pathlib.Path, required=True)
    parser.add_argument('--oracle-dir', type=pathlib.Path, required=True)
    parser.add_argument('--predictions', type=pathlib.Path, required=True)
    parser.add_argument('--out', type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        require(not args.out.exists(), 'output already exists; preserve first measurement and choose a new path')
        cases = load_cases(args.evidence_dir, args.oracle_dir)
        result = score(cases, load_json(args.predictions))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x') as output:
            output.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    except (InputError, OSError, ValueError) as exc:
        print(json.dumps({'status': 'INPUT_ERROR', 'error': str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
