import copy
import json
from pathlib import Path
import tempfile
import unittest
from prepare_run import prepare


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / 'config.json'
        source = Path(__file__).resolve().parents[1] / 'assets/scene-template.json'
        self.cfg = json.loads(source.read_text())
        for name in ('calls.csv', 'outcomes.csv', 'report.json'):
            (self.root / name).write_text('synthetic fixture')
        self.scene = self.cfg['scenes'][0]
        self.scene.update(product='NovaCare', country='KE', language='English')
        self.scene['inputs'].update(calls=['calls.csv'], outcomes=['outcomes.csv'])
        self.scene['testset']['role_labels'] = {'user': 'Customer', 'assistant': 'Agent'}
        self.scene['identity'].update(kind='exact_id', call_key='customer_id', outcome_key='customer_id')
        self.scene['outcome'].update(event='appointment_list_membership', membership_basis='Synthetic confirmed appointment list')

    def tearDown(self):
        self.tmp.cleanup()

    def run_plan(self, steps):
        return prepare(self.cfg, self.path, steps)

    def test_non_collection_does_not_require_network_settings(self):
        r = self.run_plan(['annotate', 'analyze'])
        self.assertEqual(r['status'], 'ready_for_agent_verification')
        self.assertEqual([p['step'] for p in r['plan']], ['annotate', 'analyze'])
        self.assertEqual(r['execution'], 'offline_plan_only')

    def test_non_ng_phone_rejects_ng_normalization(self):
        self.scene['identity'].update(kind='phone', normalize='ng_e164')
        self.scene['fields']['outcome_phone'] = 'phone'
        r = self.run_plan(['annotate'])
        self.assertIn('ng_e164 requires country=NG', r['plan'][0]['missing'])

    def test_rejudge_without_prompt_or_network_document(self):
        self.scene['evaluation'].update(mode='rejudge', archive='report.json', rubric={'factuality': 'evidence'}, rubric_version='1')
        self.cfg['interfaces']['api_document'] = 'absent.md'
        r = self.run_plan(['evaluate'])
        self.assertEqual(r['status'], 'ready_for_agent_verification')

    def test_unknown_scene_rejected(self):
        r = prepare(self.cfg, self.path, ['analyze'], ['absent'])
        self.assertEqual(r['status'], 'invalid')

    def test_failure_in_one_scene_keeps_independent_scene_ready(self):
        bad = copy.deepcopy(self.scene)
        bad['id'] = 'missing-input'
        bad['inputs']['calls'] = ['absent.csv']
        self.cfg['scenes'].append(bad)
        r = self.run_plan(['annotate'])
        self.assertEqual(r['plan'][0]['status'], 'ready_for_agent_verification')
        self.assertEqual(r['plan'][1]['status'], 'needs_input')

    def test_changed_interface_rejected(self):
        self.cfg['interfaces']['gateway_base_url'] = 'https://other.invalid'
        self.assertEqual(self.run_plan(['analyze'])['status'], 'invalid')

    def test_missing_mapping_cannot_look_ready(self):
        self.scene['identity'].update(kind='phone', normalize='exact')
        r = self.run_plan(['annotate'])
        self.assertEqual(r['status'], 'needs_input')

    def test_upstream_only_satisfies_planned_artifact(self):
        self.scene.update(data_source='synthetic', data_dir='output', time_window='confirmed', project_value='example:1', extract_kinds=['calls'])
        self.scene['inputs']['calls'] = []
        r = self.run_plan(['extract', 'analyze'])
        self.assertEqual(r['status'], 'ready_for_agent_verification')
        r = self.run_plan(['analyze', 'extract'])
        self.assertEqual(r['plan'][0]['status'], 'needs_input')

    def setup_multiturn(self):
        self.scene['inputs']['suite'] = 'report.json'
        self.scene['evaluation'].update(mode='generate', baseline='report.json', candidate='report.json', fixture_source='frozen', rubric={}, rubric_version=None)
        self.cfg['interfaces']['api_document'] = 'report.json'
        self.cfg['execution']['max_requests'] = 10
        self.scene['multiturn'].update(user_mode='assistant_direct', user_endpoint=None, persona_path='report.json', repeats=1, max_service_turns=3, timeout_seconds=10)
        self.scene['iteration'].update(parent_path='report.json', target_version='V2', prompt_dir='output')

    def test_roleplay_does_not_produce_report_or_require_rubric(self):
        self.setup_multiturn()
        r = self.run_plan(['multiturn', 'iterate'])
        self.assertEqual(r['plan'][0]['status'], 'ready_for_agent_verification')
        self.assertEqual(r['plan'][1]['status'], 'needs_input')

    def test_roleplay_analysis_chain_without_calls(self):
        self.setup_multiturn()
        self.scene['inputs']['calls'] = []
        self.scene['fields'] = {}
        self.scene['evaluation'].update(rubric={'uptake': '0-2'}, rubric_version='v1')
        r = self.run_plan(['multiturn', 'analyze', 'iterate'])
        self.assertEqual(r['status'], 'ready_for_agent_verification')

    def test_failed_roleplay_cannot_fall_back_to_unrelated_calls(self):
        self.setup_multiturn()
        self.scene['inputs']['suite'] = 'missing.json'
        self.scene['evaluation'].update(rubric={'uptake': '0-2'}, rubric_version='v1')
        r = self.run_plan(['multiturn', 'analyze', 'iterate'])
        self.assertTrue(all(x['status'] == 'needs_input' for x in r['plan']))

    def test_saved_roleplay_analysis_without_network_or_calls(self):
        self.scene['inputs'] = {'multiturn_archive': 'report.json'}
        self.scene['fields'] = {}
        self.cfg['interfaces']['api_document'] = 'missing.md'
        self.scene['evaluation'].update(rubric={'uptake': '0-2'}, rubric_version='v1')
        self.assertEqual(self.run_plan(['analyze'])['status'], 'ready_for_agent_verification')
        self.scene['inputs']['multiturn_archive'] = 'missing.json'
        self.assertEqual(self.run_plan(['analyze'])['status'], 'needs_input')

    def test_no_mutation(self):
        before = copy.deepcopy(self.cfg)
        self.run_plan(['annotate', 'analyze'])
        self.assertEqual(before, self.cfg)


if __name__ == '__main__':
    unittest.main()
