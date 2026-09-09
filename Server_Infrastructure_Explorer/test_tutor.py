import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import groq_tutor as gt
import learner_store as ls
from lessons import BY_ID,LESSONS
from tutor import DEFAULT_PROFILE
from streamlit.testing.v1 import AppTest

def completion(text,**extra):return {'choices':[{'message':{'content':text,**extra}}]}

class TutorTests(unittest.TestCase):
    def test_relationship_retrieval(self):
        evidence=gt.gather('How are blades connected to towers?','cpu',[])
        self.assertTrue({'blade_servers','tower_servers','network'} <= {c['topic_id'] for c in evidence})

    def test_exact_question_reaches_groq_and_web(self):
        question='what is the connection b/w blade servers and tower servers ?'
        app=AppTest.from_file('app.py',default_timeout=30).run()
        app.radio(key='page').set_value(14).run()
        app.session_state['ai_enabled']=True
        app.session_state['active_api_key']='test-only-key'
        responses=[completion(json.dumps({'answer':'Initial explanation.','needs_web':False})),completion('Both communicate through a network switch.',executed_tools=[{'type':'web_search'}])]
        with patch.object(gt,'request',side_effect=responses) as api:
            app.chat_input[0].set_value(question).run()
        self.assertFalse(app.exception)
        self.assertEqual(api.call_count,2)
        self.assertEqual(api.call_args_list[0].args[1]['messages'][-1]['content'],question)
        self.assertIn('Both communicate',app.session_state['shared_history'][-1]['content'])
        self.assertEqual(app.session_state['last_route'],'Web lookup + Groq')

    def test_missing_key_is_explicit(self):
        app=AppTest.from_file('app.py',default_timeout=30).run()
        app.radio(key='page').set_value(14).run()
        app.chat_input[0].set_value('connection b/w blade servers and tower servers?').run()
        self.assertIn('Groq is not connected',app.session_state['shared_history'][-1]['content'])

    def test_web_routing_and_personalization(self):
        responses=[completion(json.dumps({'answer':'I need to check.','needs_web':True})),completion('Checked vendor explanation.',executed_tools=[{'type':'web_search','search_results':{'results':[]}}])]
        with patch.object(gt,'request',side_effect=responses) as api:
            answer,profile,route=gt.reply(BY_ID['cpu'],'I like cricket. Explain current CPUs in Tamil.',[],DEFAULT_PROFILE,'test-key')
        self.assertEqual(profile['language'],'Tamil')
        self.assertIn('cricket',profile['interests'])
        self.assertEqual(api.call_args_list[1].args[1]['model'],'groq/compound')
        self.assertEqual(api.call_args_list[1].args[1]['compound_custom']['tools']['enabled_tools'],['web_search'])
        self.assertEqual(route,'Web lookup + Groq')
        self.assertIn('Checked vendor explanation.',answer)

    def test_web_disabled(self):
        with patch.object(gt,'request',return_value=completion(json.dumps({'answer':'Saved facts.','needs_web':True}))) as api:
            answer,_,_=gt.reply(BY_ID['cpu'],'Latest processor prices?',[],DEFAULT_PROFILE,'test-key',False)
        self.assertEqual(api.call_count,1)
        self.assertIn('disabled',answer)

    def test_no_fake_web_success(self):
        with patch.object(gt,'request',side_effect=[completion(json.dumps({'answer':'Draft.','needs_web':True})),gt.TutorError('Limit')]):
            answer,_,route=gt.reply(BY_ID['cpu'],'Latest processors?',[],DEFAULT_PROFILE,'test-key')
        self.assertIn('not been checked',answer)
        self.assertIn('unavailable',route)

    def test_persistent_profiles_are_separate(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(ls,'DB',Path(folder)/'test.sqlite3'):
            state={'profile':DEFAULT_PROFILE,'completed':{'cpu'},'chats':{},'shared_history':[],'struggles':{'ram':1},'active_api_key':'never-save-me'}
            a=ls.create(state);b=ls.create({**state,'completed':set()})
            ls.save(a,{**state,'profile':{**DEFAULT_PROFILE,'interests':'cricket'}})
            self.assertEqual(ls.restore(a)['profile']['interests'],'cricket')
            self.assertEqual(ls.restore(b)['profile']['interests'],'')
            self.assertNotIn('active_api_key',ls.restore(a))
            with self.assertRaises(ValueError):ls.restore('x'*43)

    def test_tutor_on_every_page(self):
        app=AppTest.from_file('app.py',default_timeout=30).run()
        app.radio(key='page').set_value(14).run()
        for page in range(14):
            app.radio(key='page').set_value(page).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.chat_input),0)
            app.button(key='open_tutor').click().run()
            self.assertEqual(app.session_state['page'],14)
            self.assertEqual(len(app.chat_input),1)
        app.button(key='simple_fullpage').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state['shared_history'])
        self.assertTrue(app.session_state['struggles'])
        app.radio(key='page').set_value(0).run()
        self.assertTrue(app.session_state['shared_history'])

if __name__=='__main__':unittest.main()
