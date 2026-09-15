from pathlib import Path
import json,html
import streamlit as st
import streamlit.components.v1 as components
from content import LESSONS,BY_ID,PARTS,SOURCE
import tutor
ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='HeartLab • CBSE Class 10',page_icon='🫀',layout='wide')
st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 92% 0%,#5b294033,transparent 42%),#0b1423;color:#eaf0f8}.block-container{max-width:1300px;padding-top:2rem;padding-bottom:6rem}h1,h2,h3{letter-spacing:-.035em}h1{font-size:3.4rem!important}.stMarkdown p,.stMarkdown li{line-height:1.8;font-size:1.08rem}[data-testid="stSidebar"]{background:#111e31;border-right:1px solid #283b52}.eyebrow{font-size:.78rem;letter-spacing:.19em;text-transform:uppercase;color:#f7a2b4}.hero{border-bottom:1px solid #344157;padding:1rem 0 1.8rem;margin-bottom:1.5rem}.hero p{color:#adc0d6}.stButton button{border-radius:13px}.st-key-launcher{position:fixed;bottom:25px;right:28px;width:auto;z-index:99}.st-key-launcher button{background:#e97894;color:#101d31;border-radius:35px;padding:12px 22px;font-weight:700;box-shadow:0 8px 30px #0007}.note{padding:18px 24px;background:#1c2c42;border-left:4px solid #e97894;border-radius:0 12px 12px 0}.stChatMessage{border:1px solid #2a3e55;border-radius:16px}.stChatMessage p{font-size:1.08rem}.st-key-chat_input{max-width:100%}
</style>''',unsafe_allow_html=True)
DEFAULT={'page':0,'topic':'pump','part':'','origin':0,'history':[],'done':[],'profile':{'language':'English','style':'Step by step','interests':'','avoid':''},'last_event':None,'viewer_running':True,'viewer_cutaway':False,'viewer_labels':True,'viewer_bpm':72,'viewer_flow':False}
for k,v in DEFAULT.items():
    if k not in st.session_state:st.session_state[k]=v.copy() if isinstance(v,(dict,list)) else v
if 'pending_page' in st.session_state:
    st.session_state.page=st.session_state.pop('pending_page')
def navigate(i):st.session_state.page=i
def open_tutor(topic,origin,part=''):
    st.session_state.topic=topic;st.session_state.origin=origin;st.session_state.part=part;navigate(11)
def open_model():navigate(10)
def select_page():
    i=st.session_state.page
    if i<10:st.session_state.topic=LESSONS[i]['id'];st.session_state.part=''
with st.sidebar:
    st.markdown('## 🫀 HeartLab')
    st.caption('CBSE CLASS 10 · LIFE PROCESSES')
    titles=[f'{i+1:02d}  {l["title"]}' for i,l in enumerate(LESSONS)]+['11  Interactive heart','💬  Personal tutor']
    st.radio('Study sections',range(12),format_func=lambda i:titles[i],key='page',on_change=select_page,label_visibility='collapsed')
    st.progress(len(st.session_state.done)/10)
    st.caption(f'{len(st.session_state.done)} / 10 lessons completed')
    with st.expander('Your learning preferences'):
        p=st.session_state.profile
        with st.form('preferences'):
            language=st.text_input('Language',p['language'])
            style=st.selectbox('Explanation style',['Step by step','Short answers','Use analogies'],index=['Step by step','Short answers','Use analogies'].index(p['style']))
            interests=st.text_input('Examples I enjoy',p['interests'],max_chars=120)
            avoid=st.text_input('Examples to avoid',p['avoid'],max_chars=120)
            if st.form_submit_button('Save preferences'):st.session_state.profile=dict(language=language[:60],style=style,interests=interests,avoid=avoid);st.rerun()
    with st.expander('Keep my progress'):
        st.caption('Progress stays in this browser session. Download it before leaving; no hosted student database is used.')
        backup=json.dumps({'version':1,'profile':st.session_state.profile,'done':st.session_state.done,'history':st.session_state.history},ensure_ascii=False)
        st.download_button('Download progress',backup,'heart-learning.json','application/json')
        uploaded=st.file_uploader('Restore progress',type='json',max_upload_size=1)
        if st.button('Restore this backup',disabled=uploaded is None):
            try:
                d=json.loads(uploaded.getvalue());p=d['profile'];h=d['history'];done=d['done']
                assert d.get('version')==1 and isinstance(p,dict) and isinstance(h,list) and isinstance(done,list)
                assert p.get('style') in ['Step by step','Short answers','Use analogies']
                assert all(isinstance(p.get(k),str) for k in DEFAULT['profile'])
                assert all(isinstance(m,dict) and m.get('role') in ['user','assistant'] and isinstance(m.get('content'),str) for m in h)
                st.session_state.profile={k:p[k][:160] for k in DEFAULT['profile']};st.session_state.history=[{'role':m['role'],'content':m['content'][:10000]} for m in h[-30:]];st.session_state.done=[k for k in done if isinstance(k,str) and k in BY_ID];st.rerun()
            except (ValueError,KeyError,AssertionError,TypeError):st.error('Choose a valid HeartLab progress backup.')
    st.caption('Groq tutor configured' if tutor.api_key() else 'Teacher setup needed: Groq key')
    st.markdown('[Read the NCERT chapter]('+SOURCE+')')
page=st.session_state.page
if page<10:
    l=LESSONS[page]
    st.markdown(f'<div class="hero"><div class="eyebrow">LESSON {page+1:02d} / 10</div><h1>{l["title"]}</h1><p>{l["subtitle"]}</p></div>',unsafe_allow_html=True)
    learn,practice=st.tabs(['Explore the concept','Check your understanding'])
    with learn:
        st.image(str(ROOT/'assets'/(l['id']+'.png')),width='stretch')
        st.caption('Illustrated teaching image • anatomy simplified, not to scale. Blue/red indicate oxygen-poor/rich blood; real blood is always a shade of red.')
        st.markdown(l['text'])
        st.subheader('Three things to remember')
        for point in l['points']:st.markdown('• '+point)
        st.markdown('<div class="note"><b>Try this example</b><br>'+html.escape(l['example'])+'</div>',unsafe_allow_html=True)
        st.info('Watch out: '+l['misconception'])
        st.button('Explore this in the 3D heart →',on_click=open_model)
    with practice:
        st.subheader(l['question'])
        choice=st.radio('Choose your answer',l['options'],index=None,key='q_'+l['id'])
        if st.button('Check my answer'):
            if choice is None:st.warning('Choose one answer first.')
            elif choice==l['options'][l['answer']]:st.success('Correct! '+l['why'])
            else:st.info('Try again. '+l['why'])
        st.button('Ask the tutor to explain',on_click=open_tutor,args=(l['id'],page))
    st.divider();a,b,c=st.columns([1,2,1])
    a.button('← Previous',disabled=page==0,on_click=navigate,args=(page-1,))
    if b.button('Mark lesson complete',disabled=l['id'] in st.session_state.done):st.session_state.done.append(l['id']);st.rerun()
    c.button('Next →',on_click=navigate,args=(page+1,))
elif page==10:
    st.markdown('<div class="hero"><div class="eyebrow">THE INTERACTIVE LAB</div><h1>Meet your heart.</h1><p>Turn it. Open it. Watch it work.</p></div>',unsafe_allow_html=True)
    view=st.radio('Choose a 3D view',['Realistic exterior','Teaching cutaway'],horizontal=True,key='anatomy_view')
    st.caption('Double-click the realistic heart to open/close it • Drag to rotate • Scroll/pinch to zoom • Full screen')
    offline=view=='Teaching cutaway'
    viewer=components.declare_component('cbse_heart' if offline else 'realistic_heart',path=str(ROOT/('viewer' if offline else 'viewer_realistic')))
    event=viewer(parts=[dict(id=k,title=v[0],lesson=v[1],description=v[2]) for k,v in PARTS.items()],kind='cutaway' if view=='Beating cutaway' else 'exterior',running=st.session_state.viewer_running,cutaway=True if offline else st.session_state.viewer_cutaway,labels=st.session_state.viewer_labels,bpm=st.session_state.viewer_bpm,flow=st.session_state.viewer_flow,key='heart_model' if offline else 'realistic_model',default=None)
    if isinstance(event,dict) and event.get('event_id')!=st.session_state.last_event:
        st.session_state.last_event=event['event_id']
        for name in ['running','cutaway','labels','flow']:
            if type(event.get(name)) is bool:st.session_state['viewer_'+name]=event[name]
        if isinstance(event.get('bpm'),(int,float)):st.session_state.viewer_bpm=max(40,min(140,int(event['bpm'])))
        if event.get('part') in PARTS:
            st.session_state.part=event['part'];st.session_state.topic=PARTS[event['part']][1]
            if event.get('ask'):
                st.session_state.origin=10
                st.session_state.pending_page=11
        st.rerun()
    selected=st.session_state.part
    if selected in PARTS:
        st.subheader(PARTS[selected][0]);st.write(PARTS[selected][2]);st.button('💬 Ask about '+PARTS[selected][0],on_click=open_tutor,args=(PARTS[selected][1],10,selected))
    st.caption('Textured exterior by neshallads (CC BY 4.0), stored locally with the app. Its gentle heartbeat is an illustrative deformation. Double-click opens the artist-made animated interior. Labels are approximate study markers; blood-flow dots are a separate schematic overlay.' if not offline else 'Simplified local Blender teaching model. Optional flow dots use blue/red for oxygen-poor/rich blood; real blood is always a shade of red.')
    st.button('← Back to the lessons',on_click=navigate,args=(9,))
else:
    st.markdown('<div class="eyebrow">YOUR PERSONAL STUDY SPACE</div><h1>Let’s understand it.</h1>',unsafe_allow_html=True)
    st.button('← Return to study',on_click=navigate,args=(st.session_state.origin,))
    selected=st.session_state.part
    title=PARTS[selected][0] if selected in PARTS else BY_ID[st.session_state.topic]['title']
    st.info('How can I help you understand '+title+'?')
    st.caption('The tutor uses our NCERT-aligned notes and your preferences. Chat and preferences are sent to Groq. This is educational support, not medical advice.')
    for m in st.session_state.history:
        with st.chat_message(m['role']):st.markdown(m['content'])
    c1,c2=st.columns(2);prompt=None
    if c1.button('Give me a real-world example'):prompt='Give me a real-world example of '+title+'. Explain the situation, what happens, and why.'
    if c2.button('Explain it more simply'):prompt='I did not understand '+title+'. Explain it differently with a simple example.'
    typed=st.chat_input('Ask anything about the heart and circulation…',max_chars=2500,key='chat_input')
    prompt=typed or prompt
    if prompt:
        try:
            with st.spinner('Your tutor is thinking…'):answer,profile=tutor.reply(prompt,st.session_state.topic,selected,st.session_state.history,st.session_state.profile)
            st.session_state.profile=profile;st.session_state.history.extend([{'role':'user','content':prompt},{'role':'assistant','content':answer}]);st.session_state.history=st.session_state.history[-30:];st.rerun()
        except tutor.TutorError as e:st.error(str(e))
    if st.session_state.history and st.button('Clear chat'):st.session_state.history=[];st.rerun()
if page<11:
    with st.container(key='launcher'):
        st.button('💬 Ask your tutor',key='launch_chat',on_click=open_tutor,args=(LESSONS[page]['id'] if page<10 else st.session_state.topic,page,st.session_state.part if page==10 else ''))
