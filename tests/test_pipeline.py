import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('pipeline', Path(__file__).parents[1]/'scripts/pipeline.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def edl():
    return {'scenes': [{'id':f'{i+1:02}', 'label':'observed cooking',
        'ranges':[{'start':i*20, 'end':i*20+20, 'output_seconds':10}],
        'frames':[{'second':s,'label':f'observed action {s}'} for s in (1,3,5,7,9)]} for i in range(4)]}


class PipelineTests(unittest.TestCase):
    def test_valid_edl(self):
        p.validate_edl(edl(), 80)

    def test_reject_reversed(self):
        value=edl(); value['scenes'][1]['ranges'][0]['start']=0
        with self.assertRaises(ValueError): p.validate_edl(value,80)

    def test_reject_unobserved_frames(self):
        value=edl(); value['scenes'][0]['frames'][0]['label']=''
        with self.assertRaises(ValueError): p.validate_edl(value,80)

    def test_reject_non_ten_seconds(self):
        value=edl(); value['scenes'][0]['ranges'][0]['output_seconds']=8
        with self.assertRaises(ValueError): p.validate_edl(value,80)

    def test_reject_out_of_bounds(self):
        with self.assertRaises(ValueError): p.validate_edl(edl(),50)

    def test_reject_nan(self):
        value=edl(); value['scenes'][0]['ranges'][0]['end']=float('nan')
        with self.assertRaises(ValueError): p.validate_edl(value,80)

    def test_reject_duplicate_frames(self):
        value=edl(); value['scenes'][0]['frames'][1]['second']=1
        with self.assertRaises(ValueError): p.validate_edl(value,80)

    def test_voice_protection(self):
        self.assertAlmostEqual(p.voice_tempo(39),1)
        for seconds in (10,60):
            with self.assertRaises(ValueError): p.voice_tempo(seconds)

    def test_rights_need_evidence(self):
        self.assertFalse(p.evidence_confirmed({'status':'confirmed'}))
        self.assertTrue(p.evidence_confirmed({'status':'confirmed','evidence':'user permission dated today'}))

    def test_generation_fails_closed(self):
        self.assertTrue(p.generation_errors(Path('.'), {}, {}))

    def test_generation_evidence_and_changed_reference(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            refs = [root/f'ref-{i}.dat' for i in range(6)]
            for i, ref in enumerate(refs): ref.write_bytes(str(i).encode())
            clip=root/'clip.mp4'; clip.write_bytes(b'fixture-not-media')
            cap={'model_label':'Gemini Omni Flash 1.1', 'checked_at':'2026-09-05',
                 'duration_10s':True, 'video_plus_five_images':True, 'evidence':'observed UI'}
            scenes=[{'id':f'{i:02}', 'model_label':cap['model_label'], 'task_id':f'task-{i}',
                     'evidence':'observed task', 'quality_pass':True, 'attachments_verified':True,
                     'file':str(clip), 'sha256':p.sha(clip), 'reference_video':str(refs[0]),
                     'reference_images':[str(x) for x in refs[1:]],
                     'input_sha256':{str(x):p.sha(x) for x in refs}} for i in range(1,5)]
            rights={key:{'status':'confirmed','evidence':'permission'} for key in p.RIGHTS}
            generation={'capabilities':cap, 'scenes':scenes}
            self.assertEqual(p.generation_errors(root,generation,rights),[])
            refs[0].write_bytes(b'changed')
            self.assertTrue(p.generation_errors(root,generation,rights))


if __name__ == '__main__': unittest.main()
