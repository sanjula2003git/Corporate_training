"""Offline checks: python verify_app.py (run from the AtomLab folder)."""
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET
from streamlit.testing.v1 import AppTest
from atom import describe, PRESETS
from content import LESSONS
import tutor

for p in range(1,21):
    for e in range(21):
        d=describe(p,12,e)
        assert sum(d['shells'])==e and d['charge']==p-e and d['mass']==p+12
for values in PRESETS.values():describe(*values)
assert describe(1,0,1)['mass']==1
assert describe(6,8,6)['name']=='Carbon'
assert describe(17,18,18)['charge']==-1
for values in ((0,0,0),(21,0,0),(6,-1,6),(6,6,21)):
    try:describe(*values)
    except ValueError:pass
    else:raise AssertionError('Invalid counts accepted')
for l in LESSONS:ET.parse(Path('assets')/(l['id']+'.svg'))

app=AppTest.from_file('app.py',default_timeout=15).run()
for page in range(15):
    app.radio(key='page').set_value(page).run()
    assert not app.exception,(page,app.exception)
app.radio(key='page').set_value(0).run()
app.radio(key='q_atom').set_value('3').run()
next(b for b in app.button if b.label=='Check my answer').click().run()
assert app.success
app.radio(key='page').set_value(13).run()
app.selectbox(key='preset').set_value('Sodium ion Na⁺').run()
assert app.number_input(key='p').value==11 and app.number_input(key='e').value==10
app.number_input(key='n').set_value(13).run()
assert any(m.value=='24' for m in app.metric)
app.button(key='launch_chat').click().run()
assert app.radio(key='page').value==14
app.run()  # widget cleanup must not discard the selected atom
assert app.session_state.atom_counts=={'p':11,'n':13,'e':10}
app.radio(key='page').set_value(13).run()
assert app.number_input(key='n').value==13

captured={}
def fake_request(key,payload):
    captured.update(payload)
    return {'choices':[{'message':{'content':'11 protons and 10 electrons give charge +1.'}}]}
profile={'language':'English','style':'Use analogies','interests':'','avoid':''}
with patch.object(tutor,'request',fake_request):
    answer,p=tutor.reply('I did not understand. I like cricket.','ions','electron',[],profile,describe(11,12,10))
assert p['style']=='Step by step' and p['interests']=='cricket'
assert 'atom_counts' in captured['messages'][0]['content']
assert 'Life Processes' not in captured['messages'][0]['content']
with patch.object(tutor,'request',return_value={'choices':[]}):
    try:tutor.reply('Explain ions','ions','',[],profile)
    except tutor.TutorError:pass
    else:raise AssertionError('Malformed provider response was accepted')
print('PASS: 15 pages, quiz feedback, 420 particle combinations, invalid counts, presets, atom persistence, tutor context/error handling and 13 SVG illustrations.')
