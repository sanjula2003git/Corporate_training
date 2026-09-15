import json,struct,unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import tutor
from content import LESSONS,PARTS
class HeartTests(unittest.TestCase):
    def test_model_event_opens_matching_tutor(self):
        app=AppTest.from_file('app.py').run()
        with patch('streamlit.components.v1.declare_component',return_value=lambda **kwargs:dict(event_id='test-click',part='left_ventricle',ask=True,running=False)):
            app.radio(key='page').set_value(10).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['page'],11)
        self.assertEqual(app.session_state['part'],'left_ventricle')
        self.assertEqual(app.session_state['topic'],'walls')
    def test_all_sections_and_chat_navigation(self):
        app=AppTest.from_file('app.py',default_timeout=20).run()
        for i in range(11):
            app.radio(key='page').set_value(i).run()
            self.assertFalse(app.exception)
            app.button(key='launch_chat').click().run()
            self.assertEqual(app.session_state['page'],11)
            self.assertEqual(app.session_state['origin'],i)
            self.assertEqual(len(app.chat_input),1)
    def test_personalized_live_path_with_mock(self):
        app=AppTest.from_file('app.py').run();app.button(key='launch_chat').click().run()
        with patch.object(tutor,'request',return_value={'choices':[{'message':{'content':'The pulmonary artery carries oxygen-poor blood to the lungs.'}}]}) as req:
            app.chat_input[0].set_value('I like cricket. Explain pulmonary arteries in Tamil.').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['profile']['language'],'Tamil')
        self.assertIn('cricket',app.session_state['profile']['interests'])
        self.assertIn('oxygen-poor',app.session_state['history'][-1]['content'])
        self.assertIn('pulmonary arteries',req.call_args.args[1]['messages'][-1]['content'])
    def test_no_fake_reply_when_api_fails(self):
        app=AppTest.from_file('app.py').run();app.button(key='launch_chat').click().run()
        with patch.object(tutor,'request',side_effect=tutor.TutorError('Rate limit')):app.chat_input[0].set_value('Explain valves').run()
        self.assertEqual(len(app.session_state['history']),0)
        self.assertTrue(app.error)
    def test_artist_interior_has_skin_animation_and_local_textures(self):
        raw=Path('viewer_realistic/artist-interior.glb').read_bytes()
        self.assertEqual(struct.unpack('<4sII',raw[:12]),(b'glTF',2,len(raw)))
        size=struct.unpack_from('<I',raw,12)[0];data=json.loads(raw[20:20+size])
        self.assertGreaterEqual(len(data['skins'][0]['joints']),20)
        self.assertTrue(data['animations'][0]['channels'])
        self.assertTrue(all('bufferView' in image for image in data['images']))
        self.assertIn('baseColorTexture',data['materials'][0]['pbrMetallicRoughness'])
        self.assertIn('CC BY 4.0',data['asset']['copyright'])
    def test_model_and_diagrams_complete(self):
        for l in LESSONS:
            path=Path('assets')/(l['id']+'.png')
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
        raw=Path('viewer/heart.glb').read_bytes();magic,version,length=struct.unpack('<4sII',raw[:12]);self.assertEqual((magic,version,length),(b'glTF',2,len(raw)))
        size=struct.unpack('<I',raw[12:16])[0];data=json.loads(raw[20:20+size])
        ids={n.get('extras',{}).get('part_id') for n in data['nodes']}
        self.assertTrue(set(PARTS)<=ids)
        self.assertTrue(data.get('animations'))
        self.assertEqual(sum(bool(n.get('extras',{}).get('front_cover')) for n in data['nodes']),4)
        self.assertTrue(Path('blender/CBSE_Heart.blend').is_file())
if __name__=='__main__':unittest.main()
