from pathlib import Path
import copy, html, json
import streamlit as st
import streamlit.components.v1 as components
from content import LESSONS, BY_ID, PARTS, SOURCE
from atom import PRESETS, describe
import tutor

ROOT=Path(__file__).resolve().parent
LAB=len(LESSONS); CHAT=LAB+1
st.set_page_config(page_title='AtomLab • Explore atomic structure',page_icon='⚛️',layout='wide')
st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 90% 0%,#205c6240,transparent 45%),#0b1423;color:#eaf0f8}.block-container{max-width:1400px;padding-top:2rem;padding-bottom:6rem}h1,h2,h3{letter-spacing:-.035em}h1{font-size:3.1rem!important}.stMarkdown p,.stMarkdown li{line-height:1.8}[data-testid="stSidebar"]{background:#111e31}.eyebrow{font-size:.78rem;letter-spacing:.18em;color:#79dcc8;text-transform:uppercase}.hero{border-bottom:1px solid #344157;padding:1rem 0 1.6rem;margin-bottom:1.5rem}.hero p{color:#adc0d6}.stButton button{border-radius:12px}.st-key-launcher{position:fixed;bottom:25px;right:28px;width:auto;z-index:99}.st-key-launcher button{background:#78dfc7;color:#101d31;border-radius:35px;padding:12px 22px;font-weight:700;box-shadow:0 8px 30px #0007}.note{padding:18px 24px;background:#1c2c42;border-left:4px solid #78dfc7;border-radius:0 12px 12px 0}.stChatMessage{border:1px solid #2a3e55;border-radius:16px}
</style>''',unsafe_allow_html=True)
DEFAULT={'page':0,'topic':'atom','part':'','origin':0,'history':[],'done':[],
 'profile':{'language':'English','style':'Step by step','interests':'','avoid':''},
 'last_event':None,'atom_counts':{'p':6,'n':6,'e':6}}
for key,value in DEFAULT.items():
    if key not in st.session_state:st.session_state[key]=copy.deepcopy(value)
for key in ('p','n','e'):
    if key not in st.session_state:st.session_state[key]=st.session_state.atom_counts[key]
if 'pending_atom' in st.session_state:
    counts=st.session_state.pop('pending_atom')
    st.session_state.atom_counts=counts
    for key,value in counts.items():st.session_state[key]=value
if 'pending_page' in st.session_state:st.session_state.page=st.session_state.pop('pending_page')
def navigate(i):st.session_state.page=i
def open_tutor(topic,origin,part=''):
    st.session_state.topic=topic;st.session_state.origin=origin;st.session_state.part=part;navigate(CHAT)
def select_page():
    i=st.session_state.page
    if i<LAB:st.session_state.topic=LESSONS[i]['id'];st.session_state.part=''
def apply_preset():
    st.session_state.p,st.session_state.n,st.session_state.e=PRESETS[st.session_state.preset]
def reset_charge():st.session_state.e=st.session_state.p
with st.sidebar:
    st.markdown('## ⚛️ AtomLab')
    st.caption('ATOMIC STRUCTURE · FOUNDATION FOR CLASS 10')
    titles=[f'{i+1:02d}  {l["title"]}' for i,l in enumerate(LESSONS)]+['14  Interactive atom explorer','💬  Personal tutor']
    st.radio('Study sections',range(CHAT+1),format_func=lambda i:titles[i],key='page',on_change=select_page,label_visibility='collapsed')
    st.progress(len(st.session_state.done)/LAB)
    st.caption(f'{len(st.session_state.done)} / {LAB} lessons completed')
    with st.expander('Your learning preferences'):
        p=st.session_state.profile
        with st.form('preferences'):
            language=st.text_input('Language',p['language'],max_chars=60)
            styles=['Step by step','Short answers','Use analogies']
            style=st.selectbox('Explanation style',styles,index=styles.index(p['style']))
            interests=st.text_input('Examples I enjoy',p['interests'],max_chars=120)
            avoid=st.text_input('Examples to avoid',p['avoid'],max_chars=120)
            if st.form_submit_button('Save preferences'):
                st.session_state.profile=dict(language=language,style=style,interests=interests,avoid=avoid);st.rerun()
    with st.expander('Save my learning'):
        st.caption('Progress and chat stay in this session. Download a backup to continue later.')
        backup=json.dumps({'app':'AtomLab','version':1,**{k:st.session_state[k] for k in ('profile','done','history')}},ensure_ascii=False)
        st.download_button('Download progress',backup,'atomlab-progress.json','application/json')
        uploaded=st.file_uploader('Restore progress',type='json',max_upload_size=1)
        if st.button('Restore this backup',disabled=uploaded is None):
            try:
                d=json.loads(uploaded.getvalue());p=d['profile'];h=d['history'];done=d['done']
                assert d.get('app')=='AtomLab' and d.get('version')==1
                assert isinstance(p,dict) and isinstance(h,list) and isinstance(done,list)
                assert p.get('style') in ['Step by step','Short answers','Use analogies']
                assert all(isinstance(p.get(k),str) for k in DEFAULT['profile'])
                assert all(isinstance(m,dict) and m.get('role') in ('user','assistant') and isinstance(m.get('content'),str) for m in h)
                st.session_state.profile={k:p[k][:160] for k in DEFAULT['profile']}
                st.session_state.history=[{'role':m['role'],'content':m['content'][:10000]} for m in h[-30:]]
                st.session_state.done=list(dict.fromkeys(k for k in done if isinstance(k,str) and k in BY_ID));st.rerun()
            except (ValueError,KeyError,AssertionError,TypeError):st.error('Choose a valid AtomLab progress backup.')
    st.caption('Groq tutor connected to configured credentials' if tutor.api_key() else 'Teacher setup needed: Groq key')
    st.markdown('[NCERT textbook library]('+SOURCE+')')
page=st.session_state.page
if page!=LAB:
    for key in ('p','n','e'):st.session_state[key]=st.session_state.atom_counts[key]
if page<LAB:
    l=LESSONS[page]
    st.markdown(f'<div class="hero"><div class="eyebrow">LESSON {page+1:02d} / {LAB}</div><h1>{l["title"]}</h1><p>{l["subtitle"]}</p></div>',unsafe_allow_html=True)
    learn,practice=st.tabs(['Explore the concept','Check your understanding'])
    with learn:
        st.image(str(ROOT/'assets'/(l['id']+'.svg')),width='stretch')
        st.caption('Illustrated teaching model. Sizes, distances, colours and electron positions are simplified; electrons do not follow literal circular tracks.')
        st.markdown(l['text'])
        st.subheader('Three things to remember')
        for point in l['points']:st.markdown('• '+point)
        st.markdown('<div class="note"><b>Worked example</b><br>'+html.escape(l['example'])+'</div>',unsafe_allow_html=True)
        st.info('Watch out: '+l['misconception'])
        st.button('Explore in the 3D atom →',on_click=navigate,args=(LAB,))
    with practice:
        st.subheader(l['question'])
        choice=st.radio('Choose your answer',l['options'],index=None,key='q_'+l['id'])
        if st.button('Check my answer'):
            if choice is None:st.warning('Choose one answer first.')
            elif choice==l['options'][l['answer']]:st.success('Correct! '+l['why'])
            else:st.info('Let’s work through it. '+l['why'])
        st.button('Ask the tutor to explain',on_click=open_tutor,args=(l['id'],page))
    st.divider();a,b,c=st.columns([1,2,1])
    a.button('← Previous',disabled=page==0,on_click=navigate,args=(page-1,))
    if b.button('Mark lesson complete',disabled=l['id'] in st.session_state.done):
        st.session_state.done.append(l['id']);st.rerun()
    c.button('Next →',on_click=navigate,args=(page+1,))
elif page==LAB:
    st.markdown('<div class="hero"><div class="eyebrow">THE INTERACTIVE LAB</div><h1>Build an atom.</h1><p>Change one particle. Discover what changes.</p></div>',unsafe_allow_html=True)
    st.selectbox('Start with an example',list(PRESETS),index=2,key='preset',on_change=apply_preset)
    a,b,c=st.columns(3)
    a.number_input('Protons · change the element',1,20,key='p',step=1)
    b.number_input('Neutrons · change the isotope',0,24,key='n',step=1)
    c.number_input('Electrons · change the charge',0,20,key='e',step=1)
    st.button('Make this atom neutral',on_click=reset_charge)
    d=describe(st.session_state.p,st.session_state.n,st.session_state.e)
    st.session_state.atom_counts={k:d[k] for k in ('p','n','e')}
    a,b,c,e=st.columns(4)
    a.metric('Element',d['name']);b.metric('Atomic number Z',d['p']);c.metric('Mass number A',d['mass']);e.metric('Charge',f"{d['charge']:+d}" if d['charge'] else '0')
    st.caption('Drag to rotate · Scroll/pinch or use + / − to zoom · Click or tap a particle · Double-click the nucleus to spread its particles · Full screen')
    viewer=components.declare_component('atomlab_explorer',path=str(ROOT/'viewer'))
    event=viewer(atom=d,parts=[dict(id=k,title=v[0],description=v[2]) for k,v in PARTS.items()],key='atom_explorer',default=None)
    if isinstance(event,dict) and event.get('event_id')!=st.session_state.last_event:
        st.session_state.last_event=event.get('event_id')
        counts=event.get('counts')
        if isinstance(counts,dict):
            try:
                describe(counts.get('p'),counts.get('n'),counts.get('e'))
                st.session_state.pending_atom={k:counts[k] for k in ('p','n','e')}
            except ValueError:pass
        if event.get('topic') in BY_ID:st.session_state.topic=event['topic']
        if event.get('ask') and (event.get('part') in PARTS or event.get('topic') in BY_ID):
            st.session_state.part=event['part'] if event.get('part') in PARTS else ''
            if st.session_state.part:st.session_state.topic=PARTS[st.session_state.part][1]
            st.session_state.origin=LAB;st.session_state.pending_page=CHAT
        st.rerun()
    st.info('This is a counting model for the first 20 elements. Custom combinations may be unstable or may not exist as bound atoms or ions. Shell populations use a simplified 2,8,8,2 pattern for up to 20 electrons; unusual ions may need a more advanced model. Nuclear stability and quantum motion are not simulated.')
    st.subheader('Try three discoveries')
    st.markdown('1. Compare **carbon-12 and carbon-13**. Which count changes?\n2. Compare **carbon-14 and nitrogen-14**. Why are they isobars?\n3. Compare **sodium-23 and Na⁺**. Which count stays the same?')
    st.button('← Back to revision',on_click=navigate,args=(LAB-1,))
else:
    st.markdown('<div class="eyebrow">YOUR PERSONAL STUDY SPACE</div><h1>Let’s understand it.</h1>',unsafe_allow_html=True)
    st.button('← Return to study',on_click=navigate,args=(st.session_state.origin,))
    selected=st.session_state.part
    title=PARTS[selected][0] if selected in PARTS else BY_ID[st.session_state.topic]['title']
    st.info('How can I help you understand '+title+'?')
    st.caption('The tutor uses the lesson notes, your selected atom and your preferences. Your questions and preferences are sent to Groq. It does not search the live web.')
    for m in st.session_state.history:
        with st.chat_message(m['role']):st.markdown(m['content'])
    c1,c2=st.columns(2);prompt=None
    if c1.button('Give me a real-world example'):prompt='Give me a real-world example of '+title+'. Explain what happens and why.'
    if c2.button('Explain it more simply'):prompt='I did not understand '+title+'. Use a different explanation and a simple example.'
    typed=st.chat_input('Ask about atoms, protons, neutrons, electrons…',max_chars=2500)
    prompt=typed or prompt
    if prompt:
        try:
            with st.spinner('Your tutor is thinking…'):
                answer,profile=tutor.reply(prompt,st.session_state.topic,selected,st.session_state.history,st.session_state.profile,
                    describe(**st.session_state.atom_counts))
            st.session_state.profile=profile
            st.session_state.history.extend([{'role':'user','content':prompt},{'role':'assistant','content':answer}])
            st.session_state.history=st.session_state.history[-30:];st.rerun()
        except tutor.TutorError as error:st.error(str(error))
    if st.session_state.history and st.button('Clear chat'):st.session_state.history=[];st.rerun()
if page<CHAT:
    with st.container(key='launcher'):
        st.button('💬 Ask your tutor',key='launch_chat',on_click=open_tutor,
                  args=(LESSONS[page]['id'] if page<LAB else st.session_state.topic,page,''))
