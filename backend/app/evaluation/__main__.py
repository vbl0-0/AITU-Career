"""Run with python -m app.evaluation from backend/."""
import argparse
import json
import sys

from app.evaluation.runner import run_evaluation


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline, fully judged matching evaluation; no database is accessed.')
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--baselines', nargs='+', choices=['B0', 'B1', 'B2'], default=['B0', 'B1'])
    parser.add_argument('--split', choices=['dev', 'test'], default='test')
    parser.add_argument('--k', type=int, default=5)
    parser.add_argument('--threshold', type=int, default=2)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--warmup', type=int, default=1)
    parser.add_argument('--allow-synthetic', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = run_evaluation(args.dataset, args.output, baselines=args.baselines, split=args.split,
                                k=args.k, threshold=args.threshold, repeats=args.repeats,
                                warmup=args.warmup, allow_synthetic=args.allow_synthetic)
    except (ValueError, OSError) as error:
        print('Evaluation not completed: ' + str(error), file=sys.stderr)
        return 2
    print(json.dumps({'dataset_kind': report['dataset_kind'], 'independent_quality_evidence': report['independent_quality_evidence'],
                      'baselines': list(report['baselines']), 'semantic_status': report['semantic']['status'],
                      'report': str(args.output) + '/report.json'}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
