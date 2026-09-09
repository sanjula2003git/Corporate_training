import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Understanding Digital Data", page_icon="💾", layout="wide")
st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Space+Grotesk:wght@600;700&display=swap');:root{--panel:#0e1d30;--line:#294661;--text:#edf6ff;--muted:#a9bed1;--cyan:#3bd8ff;--green:#57e3aa;--amber:#ffc866}.stApp{background:radial-gradient(circle at 85% 0%,rgba(59,216,255,.13),transparent 30%),linear-gradient(180deg,#07111f,#091725);color:var(--text);font-family:'DM Sans',sans-serif}.block-container{max-width:1200px;padding-top:1.7rem;padding-bottom:4rem}h1,h2,h3{font-family:'Space Grotesk',sans-serif!important}.hero{padding:2rem;border:1px solid var(--line);border-radius:26px;background:linear-gradient(135deg,#12263d,#081929)}.eyebrow{color:var(--cyan);font-size:.76rem;font-weight:700;letter-spacing:.14em}.hero h1{font-size:clamp(2.25rem,5vw,4.25rem);margin:.35rem 0}.hero p,.card p{color:var(--muted)}.card{height:100%;padding:1.2rem;border:1px solid var(--line);border-radius:18px;background:linear-gradient(145deg,#12263d,#0a1b2c)}.card h3{font-size:1.28rem!important;line-height:1.25;margin:.75rem 0 .45rem;word-break:normal;overflow-wrap:normal;white-space:normal}.card p{font-size:.96rem;line-height:1.5}.badge{display:inline-grid;place-items:center;min-width:35px;height:35px;padding:0 .55rem;border-radius:11px;background:rgba(59,216,255,.13);color:var(--cyan);font-weight:700}.flow{display:flex;gap:.55rem;align-items:stretch;flex-wrap:wrap;margin:1rem 0}.node{flex:1;min-width:140px;padding:1rem;border:1px solid var(--line);border-radius:16px;background:var(--panel)}.node b{color:var(--cyan)}.arrow{display:grid;place-items:center;color:var(--cyan);font-size:1.35rem}.example{padding:1rem 1.1rem;border-left:4px solid var(--amber);border-radius:0 14px 14px 0;background:rgba(255,200,102,.08)}.connection{padding:1.2rem;border:1px solid rgba(87,227,170,.35);border-radius:18px;background:rgba(87,227,170,.08)}.tag{color:var(--green);font-weight:700}div[data-testid="stSidebar"]{background:#081523;border-right:1px solid var(--line)}div[data-testid="stMetric"]{border:1px solid var(--line);background:#0e1d30;padding:1rem;border-radius:16px}</style>""",unsafe_allow_html=True)

PAGES=["1 · Meaning of Data","2 · Data vs Information","3 · Structured vs Unstructured","4 · Files and Databases","5 · Applications and Workloads","6 · Data Lifecycle","7 · Real-World Journey","8 · Visual Summary","9 · Knowledge Check"]
page=st.sidebar.radio("Unit 1.1 learning journey",PAGES)
st.sidebar.markdown("---");st.sidebar.markdown("**Unit 1.1 · Understanding Digital Data**");st.sidebar.caption("Learn every concept first. Connections to later units appear only at the end.")
st.markdown("""<div class="hero"><div class="eyebrow">UNIT 1.1 · INTERACTIVE CONCEPT LAB</div><h1>Understanding Digital Data</h1><p>Start with familiar everyday examples and learn how data gains meaning, takes different forms, is kept in files and databases, and moves through a digital lifecycle.</p></div>""",unsafe_allow_html=True);st.write("")

def cards(items):
    cols=st.columns(len(items))
    for col,(badge,title,body) in zip(cols,items): col.markdown(f"<div class='card'><span class='badge'>{badge}</span><h3>{title}</h3><p>{body}</p></div>",unsafe_allow_html=True)
def readings(): return pd.DataFrame({"Day":["Mon","Tue","Wed","Thu","Fri"],"City":["Mysuru"]*5,"Temperature (°C)":[26.1,27.0,28.7,30.4,32.1]})
def donut(labels,values,colors,title):
    fig=go.Figure(go.Pie(labels=labels,values=values,hole=.58,marker_colors=colors,textinfo="label+percent"));fig.update_layout(title=title,height=340,paper_bgcolor="rgba(0,0,0,0)",font_color="#edf6ff",margin=dict(l=20,r=20,t=55,b=20),showlegend=False);return fig
def simple_bar(labels,values,title,ytitle="Relative amount"):
    fig=go.Figure(go.Bar(x=labels,y=values,marker_color=["#3bd8ff","#57e3aa","#ffc866","#ff82a8"][:len(labels)],text=values,textposition="outside"));fig.update_layout(title=title,height=330,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#0e1d30",font_color="#edf6ff",yaxis_title=ytitle,margin=dict(l=20,r=20,t=55,b=20));return fig

if page==PAGES[0]:
    st.header("What is data?");st.markdown("**Data is a collection of raw facts, observations or measurements that can be recorded and processed.**")
    cards([("123","Numbers","Age, price, marks, distance and temperature."),("ABC","Text","Names, addresses, messages and notes."),("◉","Media","Photographs, videos and voice recordings."),("✓","Choices","Yes/no answers, ratings and selected options.")])
    st.subheader("Real-world example");st.markdown("<div class='example'><b>A thermometer displays 32.1 °C.</b><br>This value is data. By itself, it does not tell us where or when it was measured, whether it is unusually hot, or what someone should do.</div>",unsafe_allow_html=True)
    st.subheader("Where everyday data comes from");st.dataframe(pd.DataFrame([["School","Names, attendance and marks"],["Shop","Products, prices and receipts"],["Mobile phone","Contacts, messages, photographs"],["Weather station","Temperature and rainfall"],["Hospital","Appointments and test results"]],columns=["Source","Example data"]),hide_index=True,use_container_width=True)
    left,right=st.columns([1.15,.85]);left.markdown("""### Important characteristics of data
- Data can be **created by people** or **captured by devices**.
- It can describe a person, object, place, action or event.
- It may be correct, incorrect, complete or incomplete.
- One fact may have little meaning until it is combined with context.

### Why data matters
Digital applications depend on data to remember events, perform calculations, answer questions and support decisions.""");right.plotly_chart(donut(["Numbers","Text","Images","Audio/video"],[35,30,20,15],["#3bd8ff","#57e3aa","#ffc866","#ff82a8"],"Common forms of data"),use_container_width=True,config={"displayModeBar":False})
elif page==PAGES[1]:
    st.header("Data vs information");cards([("D","Data","Raw fact: 32.1 °C on Friday."),("+","Context","The reading is for Mysuru; 30 °C is considered hot in this example."),("I","Information","Friday was hotter than the chosen comparison level.")])
    st.subheader("Make information from data");df=readings();threshold=st.slider("Choose a comparison temperature (°C)",22.0,35.0,30.0,.5);latest=float(df["Temperature (°C)"].iloc[-1]);above=latest-threshold
    a,b,c=st.columns(3);a.metric("Friday's raw reading",f"{latest:.1f} °C");b.metric("Comparison level",f"{threshold:.1f} °C");c.metric("Difference",f"{above:+.1f} °C")
    (st.warning if above>0 else st.success)(f"Information: Friday was {abs(above):.1f} °C {'above' if above>0 else 'below'} the chosen comparison level.");st.info("Data becomes information when it is organized, compared, interpreted or placed in context.")
    st.subheader("Four ways data gains meaning");cards([("1","Organize","Arrange values into a list, table or timeline."),("2","Compare","Compare a value with another value, average or limit."),("3","Calculate","Find totals, differences, percentages or trends."),("4","Interpret","Explain what the result means for a person or decision.")])
    st.markdown("<div class='example'><b>Marks example:</b> 78, 84 and 91 are data. “The student's mark improved in every test” is information produced by arranging and comparing those values.</div>",unsafe_allow_html=True)
elif page==PAGES[2]:
    st.header("Structured and unstructured data");cards([("▦","Structured data","Organized into defined fields, rows and columns, making it easy to search, filter and calculate."),("▧","Unstructured data","Does not follow a fixed table format and may require people or AI to interpret its meaning.")])
    examples={"Student attendance table":("Structured","It has defined fields such as name, date and present/absent."),"Birthday video":("Unstructured","Video contains visual and audio content rather than fixed rows."),"Shop product list":("Structured","Every product follows fields such as name, price and quantity."),"Voice message":("Unstructured","Speech must be heard or transcribed to understand it."),"Online survey responses":("Structured","Each response follows the same questions and fields."),"Recipe PDF":("Unstructured","Text, pictures and page layout do not form a simple table.")}
    st.subheader("Classify an example");item=st.selectbox("Select an item",list(examples));answer=st.radio("Your answer",["Structured","Unstructured"],horizontal=True,index=None)
    if st.button("Check classification"): correct,why=examples[item];(st.success if answer==correct else st.error)(f"{correct}: {why}")
    st.dataframe(pd.DataFrame([["Asha","Present","82"],["Ravi","Absent","76"]],columns=["Student","Attendance","Marks"]),hide_index=True,use_container_width=True);st.caption("This table is structured. Photos, videos, emails and voice recordings are unstructured.")
    left,right=st.columns(2);left.markdown("""### Structured data is useful when
- Every item follows the same fields
- Values need to be sorted or filtered
- Totals and comparisons are required
- A particular record must be found quickly

**Examples:** attendance, product prices, contact lists and survey answers.""");right.markdown("""### Unstructured data is useful when
- Natural language or rich detail is important
- Information is visual or spoken
- A fixed table cannot capture the full meaning
- People need to read, watch or listen

**Examples:** essays, photographs, videos, emails and voice messages.""")
    st.plotly_chart(donut(["Structured","Unstructured"],[40,60],["#3bd8ff","#ffc866"],"Illustrative mix of everyday digital content"),use_container_width=True,config={"displayModeBar":False});st.caption("The percentages are illustrative and are used only to make the comparison visual.")
elif page==PAGES[3]:
    st.header("Files and databases");cards([("📄","File","A named collection stored as one unit, such as a PDF, image, spreadsheet, log or video."),("▤","Database","An organized collection whose records can be searched, updated and related efficiently.")])
    choices={"Save a birthday video":("File","A video is naturally kept as one media file."),"Find every student in Class 6":("Database","Student records can be searched by class."),"Keep a recipe PDF":("File","A recipe document can be saved as one file."),"Update thousands of customer addresses":("Database","A database supports repeated searches and updates."),"Save a family photograph":("File","A photograph is naturally stored as an image file.")}
    use=st.selectbox("Choose a requirement",list(choices));st.info(f"**Recommended: {choices[use][0]}** — {choices[use][1]}");st.warning("Files and databases are not opposites: applications often keep structured records in databases while storing documents and media as files.")
    st.subheader("How they behave")
    st.dataframe(pd.DataFrame([["Basic form","One named item","Collection of organized records"],["Familiar example","Photo or PDF","Student or customer record system"],["Finding information","Open or search files","Ask for matching records"],["Changing information","Edit the file","Add, update or remove records"],["Best suited to","Documents and media","Repeated, organized information"]],columns=["Feature","File","Database"]),hide_index=True,use_container_width=True)
    st.markdown("<div class='example'><b>Library example:</b> A scanned book can be one PDF file. A searchable catalogue containing each book's title, author and shelf number is a database.</div>",unsafe_allow_html=True)
elif page==PAGES[4]:
    st.header("Applications and workloads");cards([("APP","Application","A software tool people use, such as a shopping app, map, calculator or school portal."),("LOAD","Workload","The amount of work an application must perform—for example, serving ten users versus ten thousand users.")])
    users=st.slider("Simultaneous users",100,10000,2500,100);requests=st.slider("Requests per user each minute",1,20,4);total=users*requests;cpu=min(98,18+total/700);newdata=total*.006
    a,b,c=st.columns(3);a.metric("Actions each minute",f"{total:,}");b.metric("Relative work level",f"{cpu:.0f}%");c.metric("New information created",f"{newdata:.1f} MB/min")
    st.markdown("<div class='example'><b>Real-world example:</b> A shopping app may handle searches, logins and purchases. More people using it at once means more work for the application.</div>",unsafe_allow_html=True);st.info("The application is the software people use; workload describes how much work that application is doing.")
    st.plotly_chart(simple_bar(["100 users","1,000 users","5,000 users","10,000 users"],[15,30,65,95],"More users usually create more work"),use_container_width=True,config={"displayModeBar":False})
    st.subheader("Workload can change because of")
    cards([("👥","More users","More people use the application at the same time."),("↻","More actions","Each person searches, uploads or buys more frequently."),("▣","Larger data","The application handles bigger photographs, videos or records."),("⏰","Busy periods","Demand rises at particular times, such as a ticket sale.")])
elif page==PAGES[5]:
    st.header("Data creation, processing, transmission and storage");st.markdown("""<div class='flow'><div class='node'><b>1 · Creation</b><br>A person or device produces data.</div><div class='arrow'>→</div><div class='node'><b>2 · Processing</b><br>Software checks, sorts or calculates.</div><div class='arrow'>→</div><div class='node'><b>3 · Transmission</b><br>Data is sent to another place.</div><div class='arrow'>→</div><div class='node'><b>4 · Storage</b><br>A file or database keeps it.</div></div>""",unsafe_allow_html=True)
    stage=st.select_slider("Follow an online school form",options=["Creation","Processing","Transmission","Storage"]);explain={"Creation":"A teacher enters a student's name and attendance into a form.","Processing":"The application checks that all required answers are filled in.","Transmission":"The completed form is sent through the internet.","Storage":"The attendance record is saved so it can be viewed later."};st.success(explain[stage]);st.markdown("Stored data can later be opened, processed again, sent elsewhere or kept for future reference.")
    st.subheader("The same four stages in everyday activities")
    st.dataframe(pd.DataFrame([["Sending a photograph","Camera captures it","Phone adjusts it","Message sends it","Recipient saves it"],["Online purchase","Buyer enters order","App calculates total","Order is sent","Purchase is recorded"],["School attendance","Teacher enters status","App checks entries","Form is submitted","Record is saved"]],columns=["Activity","Creation","Processing","Transmission","Storage"]),hide_index=True,use_container_width=True)
    st.info("Processing does not always mean a difficult calculation. Checking spelling, sorting names, resizing a photograph and calculating a total are all forms of processing.")
elif page==PAGES[6]:
    st.header("Real-world journey: a week of weather readings");df=readings();fig=go.Figure(go.Scatter(x=df.Day,y=df["Temperature (°C)"],mode="lines+markers",line=dict(color="#3bd8ff",width=4)));fig.add_hline(y=30,line_dash="dash",line_color="#ffc866",annotation_text="Comparison level");fig.update_layout(height=350,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#0e1d30",font_color="#edf6ff",yaxis_title="Temperature (°C)");st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.dataframe(pd.DataFrame([["Create","A thermometer records each day's temperature","Numerical data"],["Process","An application compares the five readings","Data becomes information"],["Transmit","The readings are sent to a weather application","Data is moved"],["Store","The readings are saved for later comparison","Stored records"],["Use","The application shows that Friday was the hottest day","Information supports understanding"],["Preserve","A separate copy can prevent accidental loss","Later Unit 5 connection"]],columns=["Stage","What happens","Concept demonstrated"]),hide_index=True,use_container_width=True)
    st.markdown("<div class='example'><b>Outcome:</b> The learner does not merely see five numbers. The organized readings show that temperature increased during the week and Friday was the hottest day.</div>",unsafe_allow_html=True)
elif page==PAGES[7]:
    st.header("Visual summary of Unit 1.1")
    st.markdown("Use this page to revise how all six concepts fit together before taking the knowledge check.")
    st.markdown("""<div class='flow'><div class='node'><b>Raw data</b><br>Facts such as names, numbers, text and media</div><div class='arrow'>→</div><div class='node'><b>Meaning</b><br>Context and processing create information</div><div class='arrow'>→</div><div class='node'><b>Organization</b><br>Structured or unstructured form</div><div class='arrow'>→</div><div class='node'><b>Keeping it</b><br>Files and databases</div><div class='arrow'>→</div><div class='node'><b>Using it</b><br>Applications perform workloads</div></div>""",unsafe_allow_html=True)
    summary=pd.DataFrame([["Meaning of Data","Raw facts and observations","32.1 °C"],["Data vs Information","Meaning created from context","Friday was the hottest day"],["Structured/Unstructured","Whether data follows a fixed format","Attendance table / birthday video"],["Files and Databases","Ways of keeping digital data","PDF / student record system"],["Applications and Workloads","Software and the work it performs","Shopping app during a busy sale"],["Data Lifecycle","How data moves through stages","Create → process → transmit → store"]],columns=["Concept","Remember it as","Everyday example"])
    st.dataframe(summary,hide_index=True,use_container_width=True)
    left,right=st.columns(2)
    left.plotly_chart(donut(["Learn","Compare","Apply","Review"],[25,25,30,20],["#3bd8ff","#57e3aa","#ffc866","#ff82a8"],"Learning path in this app"),use_container_width=True,config={"displayModeBar":False})
    right.markdown("""### Questions to ask about any digital example
1. What raw data is being created?
2. What context turns it into information?
3. Is it structured or unstructured?
4. Is it better represented as a file or in a database?
5. Which application uses it?
6. What work must the application perform?
7. How is the data created, processed, transmitted and stored?

If you can answer these questions, you understand the core of Unit 1.1.""")
    st.info("Connections to later course units will be added after the Unit 1.1 learning content is finalized.")
else:
    st.header("Unit 1.1 knowledge check");qs=[("A raw temperature reading is…",["Data","Information","A workload"],0),("Which is unstructured?",["Attendance table","Birthday video","Product table"],1),("Best home for searchable student records?",["Database","Video file","Voice message"],0),("What is a workload?",["An application name","The amount of work an application is doing","A photograph"],1),("Correct lifecycle order?",["Store → create → transmit → process","Create → process → transmit → store","Transmit → store → create → process"],1),("Why does Unit 5 connect?",["It repeats every definition","It later explains how data is kept and protected","It removes the need for data"],1)];answers=[]
    for i,(q,opts,_) in enumerate(qs): answers.append(st.radio(f"{i+1}. {q}",opts,index=None,key=f"q{i}"))
    if st.button("Check answers"):
        if None in answers: st.warning("Answer every question first.")
        else:
            score=sum(a==opts[c] for a,(_,opts,c) in zip(answers,qs));st.metric("Score",f"{score} / {len(qs)}");(st.success if score>=5 else st.info)("Strong understanding." if score>=5 else "Review the learning pages and try again.")
