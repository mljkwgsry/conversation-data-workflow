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

    def test_no_mutation(self):
        before = copy.deepcopy(self.cfg)
        self.run_plan(['annotate', 'analyze'])
        self.assertEqual(before, self.cfg)


if __name__ == '__main__':
    unittest.main()
