import argparse
import hashlib
import json
from pathlib import Path
from evaluate import FROZEN, SOURCE_HASH, evaluate, frozen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=False)
    profile = json.loads((FROZEN / 'PROFILE.json').read_text())
    rows, predictions = [], []
    for path in sorted((FROZEN / 'scenarios').rglob('evidence.json')):
        c = json.loads(path.read_text())
        old = frozen.evaluate(c, profile, 'acder_bounded')
        new = evaluate(c, profile)
        predictions.append(new)
        oracle_path = FROZEN / 'oracles' / path.relative_to(FROZEN / 'scenarios').parent / 'oracle.json'
        oracle = json.loads(oracle_path.read_text())
        expected = {r['claim_id']: r for r in oracle['claims']}
        for a, b in zip(old['claims'], new['claims']):
            rows.append({'case_id': c['case_id'], 'claim_id': a['claim_id'],
                         'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'before': a, 'after': b, 'frozen_oracle': expected[a['claim_id']]})
    changes = [r for r in rows if r['before']['conditions'] != r['after']['conditions']]
    status_changes = [r for r in rows if any(r['before'][k] != r['after'][k] for k in ('state', 'qualification'))]
    report = {'schema': 'k1-condition-repair-report-v2', 'scope': 'Known regression data; no unseen holdout accuracy',
              'frozen_evaluator_sha256': SOURCE_HASH, 'case_count': len(predictions),
              'claim_count': len(rows), 'state_or_qualification_changes': len(status_changes),
              'condition_changes': changes, 'rows': rows,
              'source_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(Path(__file__).parent.glob('*')) if p.is_file()}}
    (out / 'comparison.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    (out / 'predictions.json').write_text(json.dumps(predictions, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: report[k] for k in ('case_count', 'claim_count', 'state_or_qualification_changes')}))
    print('Condition changes:', len(changes))


if __name__ == '__main__':
    main()
