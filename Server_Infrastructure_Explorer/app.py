from copy import deepcopy
from pathlib import Path
import html, json, os, random, re, sqlite3
import streamlit as st
import streamlit.components.v1 as components
from lessons import LESSONS, BY_ID
from knowledge import load as load_knowledge, search as search_knowledge
from tutor import DEFAULT_PROFILE, offline_reply, learn_preferences
from groq_tutor import reply as groq_reply, check_connection, TutorError
import learner_store
import cloud_store

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Server Infrastructure Explorer',page_icon='🖥️',layout='wide')
st.markdown('''<style>
.stApp{background:radial-gradient(circle at 85% -5%,#43d9ff16,transparent 33%),linear-gradient(180deg,#06111d,#091624);color:#eef8ff}
.block-container{max-width:1450px;padding-top:1.5rem;padding-bottom:3rem}
h1,h2,h3{letter-spacing:-.025em}.stMarkdown p,.stMarkdown li{font-size:1.12rem;line-height:1.75}
[data-testid="stSidebar"]{background:#081522;border-right:1px solid #294960}
.eyebrow{color:#43d9ff;font-size:.78rem;letter-spacing:.14em;font-weight:700;text-transform:uppercase}
.hero{background:linear-gradient(130deg,#142e46,#091b2b);border:1px solid #294960;border-radius:20px;padding:1.5rem 1.8rem;margin-bottom:1.25rem}.hero h1{margin:.4rem 0;font-size:clamp(2rem,4vw,3.4rem)}.hero p{color:#acc1d1;margin:0}
.bridge{border-left:4px solid #5ee5aa;padding:.85rem 1rem;background:#5ee5aa0c;margin:1rem 0;border-radius:0 10px 10px 0}
.term{border:1px solid #294960;border-radius:14px;padding:1.1rem;background:#102437;min-height:150px}.term b{color:#43d9ff}.term p{font-size:1rem;margin:.5rem 0 0;color:#acc1d1}
.flow{display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;margin:1.4rem 0}.node{flex:1;min-width:130px;border:1px solid #34708b;padding:1rem;border-radius:10px;background:#12304a;text-align:center;font-weight:600}.arrow{color:#ffc867;font-size:1.3rem}
.example{border-left:4px solid #ffc867;padding:1rem 1.2rem;background:#ffc8670b;border-radius:0 12px 12px 0;line-height:1.7;margin:1rem 0}
.stButton>button{border-radius:10px;border:1px solid #34708b;background:#12364b;color:#eef8ff}
.stButton>button:hover{border-color:#43d9ff;color:#43d9ff}
[data-testid="stChatMessage"] p{font-size:1rem;line-height:1.6}
</style>''',unsafe_allow_html=True)

defaults={'page':0,'completed':set(),'profile':deepcopy(DEFAULT_PROFILE),'profile_rev':0,'chats':{},'selected_topic':'cpu','event_seen':None,'ai_enabled':False,'ai_error':'','shared_history':[],'struggles':{},'learner_code':None,'last_route':'Local knowledge search'}
for k,v in defaults.items():
    if k not in st.session_state:st.session_state[k]=v
PAGES=[f'{i:02d} · {l["title"]}' for i,l in enumerate(LESSONS,1)]+['14 · Interactive 3D Explorer','💬 AI Tutor']
def go(n):st.session_state.page=max(0,min(14,n))
def open_tutor(topic,origin):
    st.session_state.selected_topic=topic
    st.session_state.tutor_origin=origin
    go(14)

def find_topic(topic):
    st.session_state.selected_topic=topic
    go(13)
def choose_topic(widget_key):
    st.session_state.selected_topic=st.session_state[widget_key]

def persist():
    if st.session_state.learner_code:
        try:learner_store.save(st.session_state.learner_code,st.session_state)
        except (OSError,sqlite3.Error):st.warning('Your saved profile could not be updated. This session still works.')

def restore_learner(code):
    data=learner_store.restore(code)
    for field in learner_store.FIELDS:
        if field in data:st.session_state[field]=set(data[field]) if field=='completed' else data[field]
    st.session_state.learner_code=code
    st.session_state.profile_rev+=1

def configured_key():
    key=os.getenv('GROQ_API_KEY','')
    if not key:
        try:key=st.secrets.get('GROQ_API_KEY','')
        except Exception:pass
    return key

if not st.session_state.get('groq_initialized'):
    st.session_state.groq_initialized=True
    if configured_key():
        st.session_state.active_api_key=configured_key();st.session_state.ai_enabled=True

with st.sidebar:
    st.markdown('### Server Infrastructure')
    st.caption('UNIT 5.1 · LEARNING JOURNEY')
    st.radio('Lesson pages',range(15),format_func=lambda i:PAGES[i],key='page',label_visibility='collapsed')
    st.progress(len(st.session_state.completed)/13)
    st.caption(f'{len(st.session_state.completed)} of 13 lessons completed')
    with st.expander('Your learning preferences'):
        p=st.session_state.profile;r=st.session_state.profile_rev
        st.caption('Tell the tutor what helps. Create a saved learner profile below to keep preferences between visits.')
        with st.form(f'profile_form_{r}'):
            interests=st.text_input('Examples I like',p['interests'],placeholder='Sports, music, gaming…',max_chars=160)
            avoid=st.text_input('Examples to avoid',p['avoid'],max_chars=160)
            styles=['Step by step','Short answers','Analogies'];levels=['Beginner','More technical']
            style=st.selectbox('Explanation style',styles,index=styles.index(p['style']))
            level=st.selectbox('Detail',levels,index=levels.index(p['level']))
            language=st.text_input('Preferred language',p['language'],max_chars=60)
            if st.form_submit_button('Save preferences'):
                st.session_state.profile=dict(interests=interests,avoid=avoid,style=style,level=level,language=language or 'English')
                st.session_state.profile_rev+=1;persist();st.rerun()
        if st.button('Reset learning preferences'):
            st.session_state.profile=deepcopy(DEFAULT_PROFILE);st.session_state.profile_rev+=1;persist();st.rerun()
    with st.expander('Saved learner profile'):
        if cloud_store.enabled():
            st.caption('Supabase storage selected: saved profiles are kept outside Streamlit and can survive app restarts and redeploys.')
            if st.button('Check database connection'):
                try:cloud_store.check();st.success('Supabase learner table is reachable.')
                except cloud_store.StorageError as error:st.error(str(error))
        else:
            st.caption('Local storage: on cloud hosting, profiles may be lost during a restart or redeploy. Configure Supabase for durable storage, or download a learning backup.')
        st.download_button('Download my learning backup',learner_store.export_backup(st.session_state),'learning-backup.json','application/json')
        backup=st.file_uploader('Restore a learning backup',type=['json'])
        if st.button('Restore uploaded learning',disabled=backup is None):
            try:
                data=learner_store.import_backup(backup.getvalue())
                for field,value in data.items():st.session_state[field]=set(value) if field=='completed' else value
                st.session_state.learner_code=None
                st.session_state.profile_rev+=1
                st.rerun()
            except (ValueError,TypeError,KeyError):st.error('This is not a valid learning backup. Choose a backup downloaded from this app.')
        st.caption('Optional. Saves preferences, chats, completed lessons and topics to revisit on this server. Your private recovery code opens your profile; keep it safe. API keys are not saved here.')
        if st.session_state.learner_code:
            st.success('Your learning is being saved.')
            st.code(st.session_state.learner_code)
            if st.button('Save progress now'):persist();st.success('Saved.')
            if st.button('Leave saved profile'):
                persist()
                for field in ('profile','chats','shared_history','completed','struggles'):
                    st.session_state[field]=deepcopy(defaults[field])
                st.session_state.learner_code=None;st.session_state.profile_rev+=1;st.rerun()
        elif st.button('Create my saved profile'):
            try:st.session_state.learner_code=learner_store.create(st.session_state);st.rerun()
            except (OSError,sqlite3.Error):st.error('Server storage is unavailable. You can still download a learning backup.')
        with st.form('restore_profile'):
            recovery=st.text_input('Private recovery code',type='password')
            if st.form_submit_button('Resume my learning'):
                try:restore_learner(recovery.strip());st.rerun()
                except (ValueError,OSError,sqlite3.Error):st.error('That profile could not be opened. Check your recovery code.')
        if st.session_state.struggles:
            st.caption('Topics to revisit: '+', '.join(BY_ID[k]['title'] for k in st.session_state.struggles if k in BY_ID))
    with st.expander('AI connection',expanded=not st.session_state.ai_enabled):
        st.caption('Groq powers the personalized tutor. Chat context and learning preferences are sent to Groq when connected. Web lookup uses Groq Compound and its search provider for each question when enabled. Free account limits apply.')
        st.text_input('Groq API key',type='password',key='groq_api_key',help='Use GROQ_API_KEY in server secrets for a shared deployment. Do not paste keys into chat.')
        st.checkbox('Search the web for every question',value=True,key='web_enabled')
        if st.button('Connect Groq tutor'):
            key=st.session_state.groq_api_key or configured_key()
            try:
                with st.spinner('Checking Groq…'):check_connection(key)
                st.session_state.active_api_key=key;st.session_state.ai_enabled=True;st.session_state.ai_error='';st.success('Groq tutor connected.')
            except TutorError as error:st.session_state.ai_enabled=False;st.error(str(error))
        if st.session_state.ai_enabled and st.button('Use local knowledge search'):
            st.session_state.ai_enabled=False;st.session_state.pop('active_api_key',None);st.rerun()
    with st.expander('Collected web knowledge'):
        kb=load_knowledge()
        st.caption(f"{len(kb['sources'])} sources · {len(kb['chunks'])} notes · Collected 8 September 2026")
        knowledge_topic=st.selectbox('Browse topic',list(BY_ID),format_func=lambda k:BY_ID[k]['title'],key='knowledge_topic')
        knowledge_query=st.text_input('Search saved material',key='knowledge_query',placeholder='ECC, cache, power, NVMe…')
        for item in search_knowledge(knowledge_query,knowledge_topic,6):
            st.markdown('**'+item['heading']+'**')
            st.write(item['text'])
            st.markdown(f"[{item['source_title']}]({item['url']})")
        st.download_button('Download knowledge data',json.dumps(kb,indent=2,ensure_ascii=False),'server_knowledge.json','application/json')
    st.caption('AI tutor connected' if st.session_state.ai_enabled else 'Local knowledge base · Connect AI for conversational answers')

def tutor_panel(topic_id,location):
    lesson=BY_ID[topic_id]
    st.subheader(f'Ask about {lesson["title"]}')
    st.caption('Personalized Groq tutor' if st.session_state.ai_enabled else 'Local knowledge search — source-linked notes, not generative AI')
    if not st.session_state.ai_enabled:
        st.warning('Groq is NOT connected. AI explanations and web search cannot run until you connect a Groq API key.')
        st.markdown('[Create or copy your Groq API key](https://console.groq.com/keys), then enter it below. Do not send it in chat.')
        with st.form('connect_inline_'+location):
            inline_key=st.text_input('Groq API key',type='password',key='inline_key_'+location)
            if st.form_submit_button('Activate personalized tutor'):
                try:
                    key=inline_key.strip() or configured_key()
                    with st.spinner('Verifying Groq connection…'):check_connection(key)
                    st.session_state.active_api_key=key
                    st.session_state.ai_enabled=True
                    st.session_state.ai_error=''
                    st.rerun()
                except TutorError as error:st.error(str(error))
    greeting=f'How can I help you understand {lesson["title"]}?'
    history=st.session_state.chats.setdefault(topic_id,[])
    if history:
        for m in history:
            with st.chat_message(m['role']):st.markdown(m['content'])
        st.caption(st.session_state.last_route)
    else:
        st.write(greeting)
    prompt=st.chat_input(f'Ask about {lesson["title"]}…',key='chat_'+location,max_chars=3000)
    if st.button('Show a real-world example',key='example_'+location,width='stretch'):
        prompt='Give me a real-world example with a simple situation, what this part does, and the result.'
    if st.button('Explain more simply',key='simple_'+location,width='stretch'):
        prompt='I didn’t understand. Explain it more simply with a different example.'
    if prompt:
        old=st.session_state.profile
        if re.search(r"didn['’]?t understand|don['’]?t understand|confus|simpler|more simply",prompt,re.I):
            st.session_state.struggles[topic_id]=st.session_state.struggles.get(topic_id,0)+1
        with st.spinner('Preparing an explanation…'):
            if st.session_state.ai_enabled:
                try:
                    answer,profile,route=groq_reply(lesson,prompt,st.session_state.shared_history,old,st.session_state.active_api_key,st.session_state.web_enabled,st.session_state.struggles)
                    st.session_state.last_route=route;st.session_state.ai_error=''
                except TutorError as error:
                    st.session_state.ai_error=str(error)
                    answer,profile=offline_reply(lesson,prompt,old,history)
                    answer='**Groq is unavailable. Showing saved reference notes.**\n\n'+answer
                    st.session_state.last_route='Local fallback · AI unavailable'
            else:
                profile=learn_preferences(prompt,old)
                answer='**Groq is not connected, so I have not sent your question to the AI or searched the web.** Enter your Groq API key in the connection form above, click **Activate personalized tutor**, then ask your question again.'
                st.session_state.last_route='Connection required · no AI request made'
        st.session_state.shared_history.extend([{'role':'user','content':prompt,'topic_id':topic_id},{'role':'assistant','content':answer,'topic_id':topic_id}])
        st.session_state.shared_history=st.session_state.shared_history[-20:]
        history.extend([{'role':'user','content':prompt},{'role':'assistant','content':answer}])
        st.session_state.chats[topic_id]=history[-24:]
        if profile!=old:st.session_state.profile=profile;st.session_state.profile_rev+=1
        persist();st.rerun()
    if st.session_state.ai_error:st.caption(st.session_state.ai_error)
    if history and st.button('Clear this conversation',key='clear_'+location):
        st.session_state.chats[topic_id]=[]
        st.session_state.shared_history=[m for m in st.session_state.shared_history if m.get('topic_id')!=topic_id]
        persist();st.rerun()

page=st.session_state.page
if page<13:
    lesson=LESSONS[page]
    st.markdown(f'<div class="hero"><div class="eyebrow">5.1 · LESSON {page+1:02d} OF 13</div><h1>{lesson["title"]}</h1><p>{lesson["kicker"]}</p></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="bridge"><b>What you’ll understand:</b> {lesson["summary"]}</div>',unsafe_allow_html=True)
    learn,practice=st.tabs(['Understand','Practice & check'])
    with learn:
        st.markdown(lesson['body'])
        cols=st.columns(3)
        for col,(term,definition) in zip(cols,lesson['points']):
            col.markdown(f'<div class="term"><b>{term}</b><p>{definition}</p></div>',unsafe_allow_html=True)
        st.markdown('<div class="flow">'+'<span class="arrow">→</span>'.join(f'<div class="node">{v}</div>' for v in lesson['flow'])+'</div>',unsafe_allow_html=True)
        st.caption('Conceptual sequence — actual implementations and data paths vary.')
        st.markdown(f'<div class="example"><b>Real-world example</b><br>{lesson["example"]}</div>',unsafe_allow_html=True)
        st.info(lesson['misconception'])
        with st.expander('A simple analogy'):st.write(lesson['analogy'])
        st.caption('In the final 3D model: '+lesson['spot'])
        st.button('Find this topic in 3D',key='find3d',on_click=find_topic,args=(lesson['id'],))
    with practice:
        for kind,label in [('activity','Try a situation'),('quiz','Knowledge check')]:
            st.subheader(label)
            question,options,correct,explanation=lesson[kind]
            shuffled=list(options);random.Random(lesson['id']+kind).shuffle(shuffled)
            choice=st.radio(question,shuffled,index=None,key=f'{lesson["id"]}_{kind}')
            if st.button('Check answer',key=f'check_{lesson["id"]}_{kind}'):
                if choice is None:st.warning('Choose an answer first.')
                elif choice==options[correct]:st.success('Correct. '+explanation)
                else:
                    st.info('Try again. '+explanation)
                    st.session_state.struggles[lesson['id']]=st.session_state.struggles.get(lesson['id'],0)+1;persist()
    st.divider()
    st.divider()
    a,b,c=st.columns([1,2,1])
    a.button('← Previous',disabled=page==0,on_click=go,args=(page-1,))
    if b.button('Mark this lesson complete',disabled=lesson['id'] in st.session_state.completed):
        st.session_state.completed.add(lesson['id']);persist();st.rerun()
    c.button('Next →',on_click=go,args=(page+1,),type='primary')
elif page==13:
    st.markdown('<div class="hero"><div class="eyebrow">5.1 · PAGE 14</div><h1>Interactive 3D Explorer</h1><p>One setup. Every lesson topic. Point to a part, then ask about it.</p></div>',unsafe_allow_html=True)
    st.caption('Drag to rotate • Scroll/pinch to zoom • Hover for an explanation • Click to open the matching tutor • Full screen: expand the viewer')
    viewer=components.declare_component('server_infrastructure_viewer',path=str(ROOT/'viewer'))
    with st.container():
        topic_data=json.loads((ROOT/'assets'/'topics.json').read_text())
        for t in topic_data:t['summary']=BY_ID[t['id']]['summary']
        event=viewer(topics=topic_data,selected=st.session_state.selected_topic,key='unified_server_view',default=None)
        if isinstance(event,dict) and event.get('event_id')!=st.session_state.event_seen:
            if event.get('topic_id') in BY_ID:
                st.session_state.event_seen=event['event_id'];st.session_state.selected_topic=event['topic_id'];st.rerun()
    with st.container():
        picker_key='topic_picker_'+st.session_state.selected_topic
        st.selectbox('Selected topic',list(BY_ID),index=list(BY_ID).index(st.session_state.selected_topic),format_func=lambda k:BY_ID[k]['title'],key=picker_key,on_change=choose_topic,args=(picker_key,))
        st.button('💬 Ask the tutor about this part',on_click=open_tutor,args=(st.session_state.selected_topic,13))
    st.caption('Labels follow your view and can be hidden. The architecture board is conceptual; rack, blade and tower are different server forms in one scene. Display scales are illustrative.')
    st.button('← Back to GPU / Accelerators',on_click=go,args=(12,))

else:
    st.title('💬 Server Infrastructure Tutor')
    st.caption('Your space to ask questions, explore examples and learn at your own pace.')
    st.button('← Return to lesson or model',on_click=go,args=(st.session_state.get('tutor_origin',0),))
    st.selectbox('Topic to discuss',list(BY_ID),index=list(BY_ID).index(st.session_state.selected_topic),format_func=lambda k:BY_ID[k]['title'],key='chat_topic_'+st.session_state.selected_topic,on_change=choose_topic,args=('chat_topic_'+st.session_state.selected_topic,))
    tutor_panel(st.session_state.selected_topic,'fullpage')

if page<14:
    current_topic=LESSONS[page]['id'] if page<13 else st.session_state.selected_topic
    st.markdown('<style>.st-key-chat_launcher{position:fixed;bottom:24px;right:28px;width:auto;z-index:999}.st-key-chat_launcher button{border-radius:30px;padding:14px 24px;background:#087c9c;box-shadow:0 6px 24px #0008;font-size:1.1rem}</style>',unsafe_allow_html=True)
    with st.container(key='chat_launcher'):
        st.button('💬 Chat with tutor',key='open_tutor',on_click=open_tutor,args=(current_topic,page),help='Open the full-page personalized tutor')
