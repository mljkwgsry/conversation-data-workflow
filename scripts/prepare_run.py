"""Offline configuration preflight. No network, no business-module execution."""
import argparse
import hashlib
import json
from pathlib import Path

STEPS = ('extract', 'annotate', 'analyze', 'testset', 'evaluate', 'multiturn', 'iterate')
INTERFACES = {'buildstore_url': 'https://admin.buildstore.cn/',
              'gateway_base_url': 'http://112.13.90.15:60035'}


def prepare(config, config_path, steps, selected=None):
    errors = []
    if config.get('schema_version') != 1:
        errors.append('schema_version must be 1')
    if not steps or any(x not in STEPS for x in steps) or len(set(steps)) != len(steps):
        errors.append('steps must be a nonempty ordered list of unique supported modules')
    for key, value in INTERFACES.items():
        if config.get('interfaces', {}).get(key) != value:
            errors.append('interface contract mismatch: ' + key)
    for key in ('project_id', 'output_root'):
        if not config.get(key):
            errors.append('missing ' + key)
    execution = config.get('execution', {})
    for key in ('global_max_inflight', 'request_timeout_seconds', 'max_transport_attempts'):
        value = execution.get(key)
        if type(value) is not int or value <= 0:
            errors.append(key + ' must be a positive integer')
    if execution.get('max_transport_attempts', 0) > 3:
        errors.append('max_transport_attempts exceeds contract limit 3')
    budget = execution.get('max_requests')
    if budget is not None and (type(budget) is not int or budget <= 0):
        errors.append('max_requests must be null or a positive integer')
    scenes = config.get('scenes', [])
    if not isinstance(scenes, list) or not scenes or not all(isinstance(s, dict) for s in scenes):
        return {'status': 'invalid', 'errors': errors + ['scenes must be nonempty objects'], 'plan': []}
    ids = [s.get('id') for s in scenes]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        errors.append('scene ids must be nonempty and unique')
    if selected and any(x not in ids for x in selected):
        errors.append('unknown selected scene')
    if errors:
        return {'status': 'invalid', 'errors': errors, 'plan': []}
    root = Path(config_path).resolve().parent

    def exists(value):
        return isinstance(value, str) and bool(value) and (root / Path(value).expanduser()).is_file()

    plan = []
    for scene in scenes:
        if selected and scene['id'] not in selected:
            continue
        produced = set()
        for step in steps:
            missing, warnings = [], []
            inputs = scene.get('inputs', {})
            def need(value, label):
                if value is None or value == '' or value == [] or value == {}:
                    missing.append(label)
            def artifact(kind):
                value = inputs.get(kind)
                values = value if isinstance(value, list) else [value]
                if kind in produced:
                    return
                if not values or not all(exists(v) for v in values):
                    missing.append('existing inputs.' + kind + ' (or completed upstream artifact)')
            if step == 'extract':
                kinds = scene.get('extract_kinds', ['calls', 'outcomes'])
                if not kinds or any(k not in ('calls', 'outcomes') for k in kinds):
                    missing.append('valid extract_kinds')
                for key in ('data_source', 'time_window', 'data_dir'):
                    need(scene.get(key), key)
                if 'calls' in kinds:
                    need(scene.get('project_value'), 'project_value')
                if 'outcomes' in kinds:
                    need(scene.get('list_token'), 'list_token')
                if not missing:
                    produced.update(kinds)
            elif step == 'annotate':
                artifact('calls'); artifact('outcomes')
                out = scene.get('outcome', {})
                for key in ('event', 'column', 'positive', 'negative', 'membership_basis'):
                    need(out.get(key), 'outcome.' + key)
                if out.get('positive') == out.get('negative'):
                    missing.append('distinct positive/negative labels')
                identity = scene.get('identity', {})
                if identity.get('kind') == 'exact_id':
                    for key in ('call_key', 'outcome_key'):
                        need(identity.get(key), 'identity.' + key)
                elif identity.get('kind') == 'phone':
                    norm = identity.get('normalize')
                    if norm not in ('exact', 'ng_e164'):
                        missing.append('verified identity normalization adapter')
                    if norm == 'ng_e164' and scene.get('country') != 'NG':
                        missing.append('ng_e164 requires country=NG')
                    if not scene.get('fields', {}).get('outcome_phone') and not exists(inputs.get('identity_map')):
                        for key in ('data_source', 'project_value'):
                            need(scene.get(key), key + ' for subTaskInfo lookup')
                        need(scene.get('fields', {}).get('task_keys'), 'fields.task_keys')
                        warnings.append('subTaskInfo mapping completeness must be verified during execution')
                else:
                    missing.append('identity.kind must be phone or exact_id')
                if not missing:
                    produced.add('annotated_calls')
            elif step in ('analyze', 'testset'):
                artifact('calls')
                need(scene.get('fields', {}).get('asr'), 'fields.asr')
                need(scene.get('testset', {}).get('role_labels'), 'testset.role_labels')
                if step == 'analyze':
                    warnings.append('No outcome rate without verified annotation; dialogue analysis may proceed')
                    if not missing:
                        produced.add('report')
                else:
                    t = scene.get('testset', {})
                    for key in ('real_count', 'synthetic_count'):
                        if type(t.get(key)) is not int or t[key] < 0:
                            missing.append('testset.' + key + ' must be nonnegative integer')
                    if type(t.get('max_per_call')) is not int or t['max_per_call'] < 1:
                        missing.append('testset.max_per_call must be positive')
                    need(scene.get('language'), 'language')
                    warnings.append('Actual role parsing, semantic review, sample shortages and synthetic coverage require verification')
                    if not missing:
                        produced.add('testset')
            elif step in ('evaluate', 'multiturn'):
                ev = scene.get('evaluation', {})
                if ev.get('mode') not in ('generate', 'rejudge'):
                    missing.append('evaluation.mode must be generate or rejudge')
                if ev.get('mode') == 'rejudge':
                    if not exists(ev.get('archive')):
                        missing.append('evaluation.archive must be an existing archive index file')
                else:
                    artifact('suite' if step == 'multiturn' else 'testset')
                    for key in ('baseline', 'candidate'):
                        if not exists(ev.get(key)):
                            missing.append('evaluation.' + key + ' existing prompt file for comparison')
                    need(ev.get('fixture_source'), 'evaluation.fixture_source (even if no variables)')
                    if not exists(config.get('interfaces', {}).get('api_document')):
                        missing.append('interfaces.api_document existing file')
                    if step == 'multiturn':
                        mt = scene.get('multiturn', {})
                        if mt.get('user_endpoint') != INTERFACES['gateway_base_url'] + '/v1/chat/completions':
                            missing.append('multiturn.user_endpoint must preserve current Gateway')
                        if not exists(mt.get('persona_path')):
                            missing.append('multiturn.persona_path existing file')
                        for key in ('repeats', 'max_service_turns', 'timeout_seconds'):
                            if type(mt.get(key)) is not int or mt[key] <= 0:
                                missing.append('multiturn.' + key + ' must be positive')
                        if not budget:
                            missing.append('execution.max_requests for bounded multiturn generation')
                    warnings.append('Requires actual model discovery, variable/schema checks and authorized network execution')
                need(ev.get('rubric'), 'evaluation.rubric')
                need(ev.get('rubric_version'), 'evaluation.rubric_version')
                if not missing:
                    produced.add('report')
            elif step == 'iterate':
                artifact('report')
                it = scene.get('iteration', {})
                if not exists(it.get('parent_path')):
                    missing.append('iteration.parent_path existing file')
                need(it.get('target_version'), 'iteration.target_version')
                need(it.get('prompt_dir'), 'iteration.prompt_dir')
                if not missing:
                    produced.add('candidate_prompt')
            plan.append({'scene_id': scene['id'], 'step': step,
                         'status': 'needs_input' if missing else 'ready_for_agent_verification',
                         'missing': missing, 'warnings': warnings})
    digest = hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {'status': 'needs_input' if any(p['missing'] for p in plan) else 'ready_for_agent_verification',
            'config_sha256': digest, 'execution': 'offline_plan_only', 'errors': [], 'plan': plan}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--steps', required=True, help=','.join(STEPS))
    parser.add_argument('--scenes', help='comma-separated scene ids; omitted selects config scenes')
    args = parser.parse_args()
    try:
        cfg = json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
        result = prepare(cfg, args.config, args.steps.split(','), args.scenes.split(',') if args.scenes else None)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        result = {'status': 'invalid', 'errors': [str(exc)], 'plan': []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result['status'] == 'invalid' else 1 if result['status'] == 'needs_input' else 0


if __name__ == '__main__':
    raise SystemExit(main())
