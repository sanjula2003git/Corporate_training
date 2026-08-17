import streamlit as st
from complaint_rescue import *
st.set_page_config(page_title='Complaint Rescue',page_icon='🛟',layout='wide')
st.title('🛟 From Complaint to Correction'); st.caption('Synthetic consumer-complaint coordination laboratory')
pages=['Start','Urgency is not anger','Routing','Minimum evidence','Fair remedy','Systemic warning','Resolution check','Benchmark']
stage=st.query_params.get('stage','start'); selected={p.lower().replace(' ','-'):p for p in pages}.get(stage,'Start'); page=st.sidebar.radio('Learning journey',pages,index=pages.index(selected))
text=st.sidebar.text_area('Complaint text',Complaint().text,height=150); amount=st.sidebar.number_input('Purchase value (₹)',100,100000,4800); contacts=st.sidebar.slider('Previous contacts',0,8,3); days=st.sidebar.slider('Days open',0,30,5)
invoice=st.sidebar.checkbox('Invoice available',True); video=st.sidebar.checkbox('Video available',True); serial=st.sidebar.checkbox('Serial number available',False)
comp=Complaint(text=text,amount=amount,previous_contacts=contacts,days_open=days,invoice_available=invoice,video_available=video,serial_available=serial); result=recommend(comp)
if page=='Start':
    st.header('One accountable case'); a,b,c=st.columns(3); a.metric('Priority',result['priority']); b.metric('Owner',result['owner']); c.metric('Deadline',f"{result['deadline_hours']} hours"); st.info(result['next_action'])
elif page=='Urgency is not anger':
    rows=pd.DataFrame([{'complaint':'Angry late parcel','urgency_score':urgency(Complaint(text='I am extremely angry that my package arrived one day late.',previous_contacts=0,days_open=1))['score']},{'complaint':'Calm burning smell','urgency_score':urgency(Complaint(text='The charger became hot and made a faint burning smell.',previous_contacts=0,days_open=0))['score']}]); st.plotly_chart(fig_urgency(rows),use_container_width=True); st.caption('Safety facts outrank emotional intensity.')
elif page=='Routing': st.header(result['owner']); st.write('Supporting teams:',result['supporting']); st.write('Reasons:',result['reasons'])
elif page=='Minimum evidence':
    st.dataframe(result['documents'],hide_index=True,use_container_width=True)
    if result['missing']: st.warning(result['next_action'])
    else: st.success('Minimum evidence is available.')
elif page=='Fair remedy': st.header('Policy-eligible options'); st.write(result['remedies']); st.warning('An employee applies approved policy and applicable law; the model cannot invent or deny rights.')
elif page=='Systemic warning':
    days_x=np.arange(1,31); counts=np.maximum(0,np.round(np.linspace(1,14,30)+np.sin(days_x/3))).astype(int); st.plotly_chart(fig_systemic(days_x,counts),use_container_width=True); st.error('SYSTEMIC ISSUE ALERT — investigate MX-210 motor overheating; do not automatically declare a defect.')
elif page=='Resolution check':
    delivered=st.checkbox('Remedy delivered'); informed=st.checkbox('Customer informed'); checks,closed=resolution_check(True,delivered,informed,True,False); st.table(checks.to_frame())
    if closed: st.success('Case may close')
    else: st.error('Keep case open')
else: compdf=compare_systems(); st.plotly_chart(fig_compare(compdf),use_container_width=True); st.dataframe(compdf,hide_index=True,use_container_width=True); st.caption('Illustrative synthetic outcomes only.')
