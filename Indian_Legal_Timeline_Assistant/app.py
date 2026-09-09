"""Educational prototype: find the criminal law in force on an incident date."""
from datetime import date
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Indian Legal Timeline Assistant",page_icon="⚖️",layout="wide")
IPC_URL="https://www.indiacode.nic.in/handle/123456789/12850?locale=en"
IPC_379_URL="https://www.indiacode.nic.in/show-data?actid=AC_CEN_5_23_00037_186045_1523266765688&orderno=436&sectionId=46162&sectionno=379"
BNS_URL="https://www.indiacode.nic.in/bitstream/123456789/20062/1/a202345.pdf"
BNS_PAGE="https://www.indiacode.nic.in/indiacode/handle/123456789/20062?col=123456789%2F1362&view_type=search"
SC_URL="https://api.sci.gov.in/supremecourt/2020/2941/2941_2020_1_1501_37575_Judgement_23-Aug-2022.pdf"
BNS_START=date(2024,7,1)
ASSET_DIR=Path(__file__).parent/"assets"

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
:root{--ink:#edf4fa;--muted:#9db0c2;--line:rgba(151,177,199,.18);--panel:#111b26;--cyan:#55d4ff;--amber:#ffc15c;--green:#61d6a6}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}.stApp{color:var(--ink);background:radial-gradient(circle at 85% -5%,rgba(51,151,184,.19),transparent 34%),#08111a}
.block-container{max-width:1160px;padding-top:2.1rem;padding-bottom:4rem}h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;letter-spacing:-.025em}p,li{line-height:1.58}
.hero{padding:1.7rem;border:1px solid var(--line);border-radius:24px;background:linear-gradient(135deg,#162636,#0c1721);overflow:hidden}.eyebrow{color:var(--cyan);letter-spacing:.14em;font-size:.74rem;font-weight:800}.hero h1{font-size:clamp(2rem,4vw,3.4rem);margin:.55rem 0}.hero p{color:#bdd0de;font-size:1.06rem;max-width:760px}
.flow{display:flex;gap:.7rem;align-items:center;flex-wrap:wrap;margin-top:1rem}.chip{padding:.55rem .8rem;border:1px solid var(--line);border-radius:11px;background:rgba(255,255,255,.035)}
.card{padding:1rem 1.1rem;border:1px solid var(--line);border-radius:16px;background:rgba(17,27,38,.82);height:100%;overflow-wrap:anywhere}.card b{color:var(--cyan)}.warning-card{padding:1rem 1.1rem;border-left:4px solid var(--amber);background:rgba(255,193,92,.08);border-radius:5px 15px 15px 5px}
div[data-testid="stSidebar"]{background:#0d1822;border-right:1px solid var(--line)}div[data-baseweb="select"]>div{background:#152432;border-radius:12px}div[data-testid="stPlotlyChart"]{border:1px solid var(--line);border-radius:18px;overflow:hidden;background:#0e1721}.stButton button{border-radius:12px;min-height:46px;font-weight:700}
</style>""",unsafe_allow_html=True)

PAGES=["Overview","1 · Collect and clean data","2 · Run the legal-date model","3 · Evaluate the model","4 · Common report"]
page=st.sidebar.selectbox("Project stage",PAGES)
st.sidebar.markdown("---")
st.sidebar.caption("Educational legal-research prototype. Not legal advice, a judgment or a sentencing tool.")

def hero():
    st.markdown("""<div class='hero'><div class='eyebrow'>TEMPORAL LEGAL RESEARCH ASSISTANT</div><h1>⚖️ Indian Legal Timeline Assistant</h1><p>Find the law that was in force when an alleged incident happened—then compare it with later legal changes.</p><div class='flow'><div class='chip'>Case facts</div><span>→</span><div class='chip'>Incident date</div><span>→</span><div class='chip'>Law in force</div><span>→</span><div class='chip'>Cited issue report</div></div></div>""",unsafe_allow_html=True)

def defaults():
    return dict(incident_date=date(2020,12,31),location="Bengaluru, Karnataka",description="Gold jewellery was allegedly removed from a house without the owner's consent.",value=800000,inside_home=True,force=False,entrusted=False,employee=False)

def sample_case_data():
    """Small teaching dataset containing common data-quality problems."""
    return pd.DataFrame([
        ["CASE-101","2020-12-31","Bengaluru","theft",800000,"House complaint"],
        ["CASE-102","2024-08-10","Mysuru","theft",45000,"Shop complaint"],
        ["CASE-102","2024-08-10","Mysuru","theft",45000,"Shop complaint"],
        ["CASE-103","2023-04-18",None,"robbery",120000,"Street complaint"],
        ["CASE-104","2022-07-09","Hubballi","theft",99999999,"Value entered incorrectly"],
        ["CASE-105","2025-01-22","Mangaluru","breach of trust",None,"Property was entrusted"],
    ],columns=["case_id","incident_date","location","case_type","property_value_inr","short_note"])

def clean_case_data(raw):
    """Demonstrate a simple, visible cleaning pipeline."""
    cleaned=raw.drop_duplicates().copy()
    cleaned["location"]=cleaned["location"].fillna("Unknown")
    median_value=cleaned["property_value_inr"].median()
    cleaned["property_value_inr"]=cleaned["property_value_inr"].fillna(median_value)
    upper_limit=cleaned["property_value_inr"].quantile(.90)
    cleaned["property_value_inr"]=cleaned["property_value_inr"].clip(upper=upper_limit)
    encoded=pd.get_dummies(cleaned,columns=["case_type"],prefix="case_type",dtype=int)
    return cleaned,encoded,median_value,upper_limit

if "case" not in st.session_state: st.session_state.case=defaults()

def analyse(c):
    old=c["incident_date"]<BNS_START
    issues=[]
    if c["inside_home"]: issues.append("Theft from a dwelling may require a separate, more specific provision review.")
    if c["force"]: issues.append("Force or threat may change the classification; robbery-related provisions must be checked.")
    if c["entrusted"]: issues.append("Entrustment may point toward criminal breach of trust rather than ordinary theft.")
    if c["employee"]: issues.append("An employee or servant role may trigger a specific provision.")
    if not issues: issues.append("Ordinary theft is a starting point, but every offence ingredient still requires verification.")
    return dict(old=old,primary="Indian Penal Code, 1860 (IPC)" if old else "Bharatiya Nyaya Sanhita, 2023 (BNS)",section="IPC sections 378/379" if old else "BNS section 303",issues=issues)

def run_legal_date_model(c):
    """Hybrid retrieval + exact date-rule demonstration."""
    legal_library=pd.DataFrame([
        ["IPC","Indian Penal Code, 1860",date(1862,1,1),date(2024,6,30),"Sections 378/379","theft property dishonest taking"],
        ["BNS","Bharatiya Nyaya Sanhita, 2023",date(2024,7,1),None,"Section 303","theft property dishonest taking"],
    ],columns=["law","full_name","starts_on","ends_on","starting_section","search_terms"])
    words=set(c["description"].lower().replace(".","").replace(",","").split())
    legal_library["retrieval_matches"]=legal_library["search_terms"].apply(
        lambda text: len(words.intersection(text.split()))
    )
    retrieved=legal_library[legal_library["retrieval_matches"]>0].copy()
    if retrieved.empty:
        retrieved=legal_library.copy()
    incident=c["incident_date"]
    retrieved["date_matches"]=retrieved.apply(
        lambda row: incident>=row["starts_on"] and (row["ends_on"] is None or incident<=row["ends_on"]),axis=1
    )
    selected=retrieved[retrieved["date_matches"]].iloc[0]
    return legal_library,retrieved,selected

def date_rule_evaluation():
    tests=pd.DataFrame([
        ["TEST-01",date(2020,12,31),"IPC"],
        ["TEST-02",date(2024,6,30),"IPC"],
        ["TEST-03",date(2024,7,1),"BNS"],
        ["TEST-04",date(2024,7,2),"BNS"],
        ["TEST-05",date(2025,1,15),"BNS"],
    ],columns=["test_case","incident_date","expected_law"])
    tests["predicted_law"]=tests["incident_date"].apply(lambda value:"IPC" if value<BNS_START else "BNS")
    tests["result"]=tests.apply(lambda row:"Pass" if row["expected_law"]==row["predicted_law"] else "Fail",axis=1)
    return tests

def report_quality_checks(report,c,a):
    if not report:
        return None
    lower=report.lower()
    checks=[
        ["Incident date included",c["incident_date"].strftime("%d %B %Y").lower() in lower],
        ["Selected law included",("ipc" if a["old"] else "bns") in lower],
        ["Official source link included","indiacode.nic.in" in lower],
        ["Limitation or review warning included",("not legal advice" in lower) or ("human review" in lower) or ("lawyer" in lower)],
    ]
    return pd.DataFrame(checks,columns=["check","passed"])

def timeline(c):
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=[date(2018,1,1),BNS_START,date(2026,12,31)],y=[1,1,1],mode="lines",line=dict(color="#60788e",width=8),hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[c["incident_date"]],y=[1],mode="markers+text",text=["Incident"],textposition="top center",marker=dict(size=22,color="#ffc15c",line=dict(color="white",width=2))))
    fig.add_trace(go.Scatter(x=[BNS_START],y=[1],mode="markers+text",text=["BNS commenced"],textposition="bottom center",marker=dict(size=20,color="#55d4ff",symbol="diamond")))
    fig.add_annotation(x=date(2021,1,1),y=1.18,text="IPC period",showarrow=False,font=dict(color="#61d6a6",size=16))
    fig.add_annotation(x=date(2025,7,1),y=1.18,text="BNS period",showarrow=False,font=dict(color="#55d4ff",size=16))
    fig.update_yaxes(visible=False,range=[.65,1.35]);fig.update_xaxes(title="Legal timeline",gridcolor="rgba(255,255,255,.07)")
    fig.update_layout(height=310,paper_bgcolor="#08111a",plot_bgcolor="#0e1721",font=dict(color="#edf4fa"),showlegend=False,margin=dict(l=30,r=30,t=35,b=50))
    return fig

def legal_date_illustration():
    """Beginner-friendly overview of why the incident date matters."""
    fig=go.Figure()

    # Main legal timeline.
    fig.add_trace(go.Scatter(
        x=[8,92],y=[2.2,2.2],mode="lines",
        line=dict(color="#60788e",width=10),hoverinfo="skip",showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[24],y=[2.2],mode="markers",
        marker=dict(size=24,color="#ffc15c",line=dict(color="#edf4fa",width=2)),
        hovertemplate="Alleged incident: 31 December 2020<extra></extra>",showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[66],y=[2.2],mode="markers",
        marker=dict(size=24,color="#55d4ff",symbol="diamond",line=dict(color="#edf4fa",width=1)),
        hovertemplate="BNS began: 1 July 2024<extra></extra>",showlegend=False
    ))

    # Clearly separated old-law and later-law regions.
    fig.add_shape(type="rect",x0=7,x1=65,y0=.55,y1=1.35,
                  fillcolor="rgba(97,214,166,.13)",line=dict(color="#61d6a6",width=2))
    fig.add_shape(type="rect",x0=67,x1=93,y0=.55,y1=1.35,
                  fillcolor="rgba(85,212,255,.10)",line=dict(color="#55d4ff",width=2))
    fig.add_shape(type="line",x0=66,x1=66,y0=.35,y1=3.45,
                  line=dict(color="#55d4ff",width=2,dash="dash"))

    fig.add_annotation(x=24,y=3.15,text="ALLEGED INCIDENT<br><b>31 Dec 2020</b>",showarrow=True,
                       ax=0,ay=-58,arrowcolor="#ffc15c",arrowwidth=3,
                       bgcolor="#172432",bordercolor="#ffc15c",borderpad=8,
                       font=dict(color="#edf4fa",size=14),align="center")
    fig.add_annotation(x=66,y=3.15,text="LAW CHANGE STARTS<br><b>1 Jul 2024</b>",showarrow=True,
                       ax=0,ay=-58,arrowcolor="#55d4ff",arrowwidth=3,
                       bgcolor="#172432",bordercolor="#55d4ff",borderpad=8,
                       font=dict(color="#edf4fa",size=14),align="center")
    fig.add_annotation(x=36,y=.95,text="<b>IPC period</b><br>The incident falls here",
                       showarrow=False,font=dict(color="#edf4fa",size=16),align="center")
    fig.add_annotation(x=80,y=.95,text="<b>BNS period</b><br>Later law",
                       showarrow=False,font=dict(color="#edf4fa",size=16),align="center")
    fig.add_annotation(x=24,y=1.72,text="Use the law in force<br>on the incident date",
                       showarrow=True,ax=105,ay=-4,arrowcolor="#61d6a6",arrowwidth=3,
                       bgcolor="#10251f",bordercolor="#61d6a6",borderpad=8,
                       font=dict(color="#edf4fa",size=14),align="left")

    fig.update_xaxes(visible=False,range=[0,100])
    fig.update_yaxes(visible=False,range=[0,4.25])
    fig.update_layout(
        title="The date decides which law to check first",
        height=455,paper_bgcolor="#08111a",plot_bgcolor="#0e1721",
        font=dict(color="#edf4fa"),showlegend=False,
        margin=dict(l=30,r=30,t=72,b=25)
    )
    return fig

def report_text(c,a):
    issues="\n".join(f"- {i}" for i in a["issues"])
    return f"""# Temporal Legal Issue Report

## 1. Case summary
- Alleged incident date: {c['incident_date'].strftime('%d %B %Y')}
- Location: {c['location']}
- Description: {c['description']}
- Approximate property value: ₹{c['value']:,.0f}

## 2. Law-in-force result
- Starting substantive law: {a['primary']}
- Initial provision to examine: {a['section']}
- BNS general commencement date: 1 July 2024

## 3. Issues requiring legal review
{issues}

## 4. Temporal-law warning
The incident date must be checked against the effective date of every relied-on provision. A later, harsher criminal punishment should not be applied automatically to an earlier act. Later beneficial changes, saving clauses, special laws, state amendments and procedural questions require lawyer verification.

## 5. Official sources
- IPC: {IPC_URL}
- IPC section 379: {IPC_379_URL}
- BNS: {BNS_URL}
- BNS enforcement metadata: {BNS_PAGE}
- Supreme Court Article 20(1) discussion: {SC_URL}

## 6. Limitation
This educational report does not decide guilt, identify every offence, determine sentence or replace professional legal advice.
"""

def generate_llm_report(c,a,model_name,ollama_host="http://localhost:11434"):
    """Generate a report from verified context; the LLM does not select the legal period."""
    from ollama import Client
    verified_context=f"""VERIFIED CASE CONTEXT
Incident date: {c['incident_date'].strftime('%d %B %Y')}
Location: {c['location']}
Allegation: {c['description']}
Approximate property value: INR {c['value']:,.0f}
Selected starting law: {a['primary']}
Starting provision to examine: {a['section']}
BNS general commencement date: 1 July 2024
Issues flagged by the rule system: {'; '.join(a['issues'])}

OFFICIAL SOURCE LINKS
IPC: {IPC_URL}
IPC section 379: {IPC_379_URL}
BNS: {BNS_URL}
BNS commencement metadata: {BNS_PAGE}
Supreme Court Article 20(1) discussion: {SC_URL}
"""
    instructions="""Draft a concise educational Indian legal issue report from the supplied verified context.
Do not change or recalculate the selected legal period. Do not decide guilt or sentence.
Do not invent facts, sections, quotations, judgments or source links.
Clearly label uncertainty and matters requiring a lawyer's review.
Use these headings: Case summary; Date and starting law; Provision to examine; Issues requiring review; Sources; Limitations.
Include the supplied official URLs as Markdown links. End with: This educational draft is not legal advice."""
    client=Client(host=ollama_host)
    response=client.chat(
        model=model_name,
        messages=[
            {"role":"system","content":instructions},
            {"role":"user","content":verified_context},
        ],
        options={"temperature":0.1},
    )
    return response.message.content

def ollama_explainer():
    st.markdown("### What is Ollama?")
    st.markdown("""Ollama is a program that helps your computer run an AI language model.

Think of it this way:

- **Ollama is the runner.** It starts, stops and manages the AI model.
- **Llama 3.2 is the language model.** It reads the instructions and writes the report.
- **Streamlit is the screen you use.** It collects the case details and displays the result.

The Llama 3.2 model is downloaded to your computer once. When you request a report, Streamlit sends the verified case information to Ollama through a private address on the same computer called `localhost`. Ollama gives the information to Llama 3.2, receives the generated report and sends it back to Streamlit.

The report can therefore be created without sending the case prompt to a paid cloud-model API. However, the local model can still make mistakes, so a qualified person must review the report.""")
    st.markdown("### What is Llama 3.2?")
    st.markdown("""**Llama** is a family of AI language models created by Meta. A language model learns patterns from large amounts of text and uses those patterns to predict what text should come next.

This project uses the **Llama 3.2 3B instruction model** through Ollama:

- **3B** means that the model contains about three billion learned parameters.
- **Instruction model** means it was additionally trained to follow requests and answer in a helpful format.
- **Text model** means it accepts text and produces text. It does not see images in this project.
- It is a **static model**. It does not automatically know about events or legal changes after its training data ended.""")
    st.markdown("#### Glossary")
    term1,term2=st.columns(2)
    term1.markdown("<div class='card'><b>Learned parameters</b><br>Numbers adjusted while the model was trained. They help the model recognize language patterns and decide what text may come next.</div>",unsafe_allow_html=True)
    term2.markdown("<div class='card'><b>Static model</b><br>A model whose learned information does not update by itself. It must be given current information or replaced with a newer model.</div>",unsafe_allow_html=True)
    st.markdown("#### How Llama changes a request into an answer")
    st.markdown("""<div class='flow'>
    <div class='chip'><b>1 · Request</b><br>Receives the text</div><span>→</span>
    <div class='chip'><b>2 · Small pieces</b><br>Splits text into tokens</div><span>→</span>
    <div class='chip'><b>3 · Find patterns</b><br>Uses learned parameters</div><span>→</span>
    <div class='chip'><b>4 · Predict</b><br>Chooses the next token</div><span>→</span>
    <div class='chip'><b>5 · Repeat</b><br>Builds the full answer</div>
    </div>""",unsafe_allow_html=True)

    with st.expander("What is inside the downloaded model?",expanded=True):
        st.markdown("""- **Tokenizer:** A converter that breaks sentences into small pieces called tokens.
- **Parameters or weights:** Billions of learned numbers. They store language patterns—not readable copies of laws arranged like files.
- **Transformer layers:** Repeated processing stages that connect the meaning of different tokens in the prompt.
- **Attention mechanism:** Helps the model decide which earlier words are important while generating the next word.
- **Prompt template:** Marks which text is an instruction and which text comes from the user.
- **Model configuration:** Technical settings describing the model’s size, layers and supported context.

The download does **not** contain a live connection to Indian legal websites. Official laws must be supplied separately by the application.""")

    with st.expander("How was Llama taught?",expanded=False):
        st.markdown("""1. **Pretraining:** The model studied a very large collection of text and learned to predict missing or next tokens.
2. **Instruction tuning:** It was shown examples of instructions and useful responses.
3. **Human-preference training:** Feedback was used to encourage more helpful and safer answers.
4. **Knowledge transfer:** For Llama 3.2’s small text models, outputs from larger Llama models were also used as training targets.

Training creates the model’s parameters. When we use the app, we are not training Llama again—we are only asking the already-trained model to generate a response.""")

    with st.expander("How does Llama create this report step by step?",expanded=True):
        st.markdown("""1. **Receive verified context:** The prompt contains the incident facts, date-rule result, starting provision, warnings and official links.
2. **Split text into tokens:** Words may remain whole or be divided into smaller pieces.
3. **Turn tokens into numbers:** Each token becomes a numerical representation the model can process.
4. **Process the relationships:** Transformer layers use attention to examine how the tokens relate—for example, linking the incident date with the selected IPC period.
5. **Score the next token:** The model calculates probabilities for many possible next tokens.
6. **Choose one token:** A generation setting such as temperature influences how predictable or varied the choice is. This app uses a low temperature of `0.1` for a more consistent draft.
7. **Repeat:** The new token is added to the context, and the model predicts the next one. This continues until the report is complete.
8. **Return readable text:** Ollama joins the tokens into text and sends the report back to Streamlit.

The model can still produce confident-looking errors. The date rule, restricted prompt, official links and human review reduce risk but do not guarantee correctness.""")

    with st.expander("Simple glossary",expanded=False):
        st.markdown("""**Token** — A small piece of text processed by the model.

**Parameter or weight** — A learned number that influences the model’s predictions.

**Transformer** — The model design that processes relationships between tokens.

**Attention** — The mechanism that helps the model focus on relevant parts of the prompt.

**Context** — The information currently provided to the model for one request.

**Context window** — The maximum amount of text the model can consider in one request.

**Temperature** — A setting that controls how predictable or varied generated text can be.

**Quantization** — Storing model weights with fewer bits so the model uses less memory, usually with a small quality trade-off.""")
    st.caption("Technical reference: Meta’s official Llama 3.2 model card describes the 1B and 3B text models as autoregressive transformer models with instruction-tuned versions.")
    st.markdown("### Why was it chosen?")
    why1,why2,why3=st.columns(3)
    why1.markdown("<div class='card'><b>No API payment</b><br>After downloading the model, reports are generated on your computer without a per-report API charge.</div>",unsafe_allow_html=True)
    why2.markdown("<div class='card'><b>Runs locally</b><br>The demonstration’s case text does not need to be sent to a commercial cloud-model API.</div>",unsafe_allow_html=True)
    why3.markdown("<div class='card'><b>Easy to experiment</b><br>You can replace Llama 3.2 with another installed Ollama model by changing its name.</div>",unsafe_allow_html=True)
    st.caption("Ollama still uses your disk space, memory, processor and electricity. Local models can still produce incorrect text.")
    st.markdown("### How does it work?")
    st.markdown("1. The date rule selects the legal period.\n2. Streamlit builds a prompt containing the verified facts and official links.\n3. The prompt is sent to Ollama at `localhost:11434`.\n4. Llama 3.2 breaks the text into small pieces called **tokens**.\n5. It creates the report one token at a time.\n6. Ollama returns the draft to Streamlit for display and download.")
    st.markdown("### Video · What happens inside Ollama?")
    video_path=ASSET_DIR/"ollama-inside-explainer.mp4"
    if video_path.exists():
        st.video(str(video_path))
        st.caption("A silent 24-second animation. All explanations appear on screen.")
    else:
        st.warning("The Ollama explainer video file could not be found.")

hero()
c=st.session_state.case
a=analyse(c)

if page=="Overview":
    st.markdown("## The problem")
    st.markdown("""<div class='warning-card'><b>A new law does not always start on the day it is passed.</b><br><br>If an alleged offence happened before a legal change, lawyers must retrieve the version actually in force on the incident date. Missing this date issue can delay the case.</div>""",unsafe_allow_html=True)
    st.plotly_chart(legal_date_illustration(),use_container_width=True,config={"displayModeBar":False})
    st.warning("**Look at the dates.** The alleged incident happened in 2020, before BNS began in 2024. The legal review should therefore start with the IPC that applied on the incident date.")
    st.markdown("### Simple glossary")
    g1,g2=st.columns(2)
    g1.markdown("<div class='card'><b>IPC — Indian Penal Code</b><br>India’s earlier main criminal law. It is checked here because the example incident happened in 2020.</div>",unsafe_allow_html=True)
    g2.markdown("<div class='card'><b>BNS — Bharatiya Nyaya Sanhita</b><br>India’s newer main criminal law. It generally started applying from 1 July 2024.</div>",unsafe_allow_html=True)
    st.markdown("## What this prototype does")
    cols=st.columns(4)
    for col,(n,t,d) in zip(cols,[("01","Reads","incident facts"),("02","Checks","the legal date"),("03","Compares","old and later law"),("04","Creates","a common report")]): col.markdown(f"<div class='card'><b>{n} · {t}</b><br>{d}</div>",unsafe_allow_html=True)

elif page==PAGES[1]:
    st.markdown("## Phase 1 · Collect and clean the case data")
    st.write("First, collect the known facts. Then check the dataset before using it to find the applicable law.")
    st.markdown("### A · Data collection")
    st.markdown("""<div class='card'><b>What do we collect?</b><br>The case number, incident date, place, short description, property value and facts that may change the legal section. Each case becomes one row in the dataset.</div>""",unsafe_allow_html=True)
    with st.form("facts"):
        incident_date=st.date_input("When did the alleged incident happen?",c["incident_date"])
        location=st.text_input("Where did it happen?",c["location"])
        description=st.text_area("What allegedly happened?",c["description"],height=120)
        value=st.number_input("Approximate property value (₹)",min_value=0,value=int(c["value"]),step=1000)
        x,y=st.columns(2)
        inside_home=x.checkbox("Taken from a house or building",c["inside_home"]);force=y.checkbox("Force or threat was used",c["force"])
        entrusted=x.checkbox("Property was entrusted to the accused",c["entrusted"]);employee=y.checkbox("Accused was an employee or servant",c["employee"])
        if st.form_submit_button("Analyse the legal date",use_container_width=True):
            st.session_state.case=dict(incident_date=incident_date,location=location,description=description,value=value,inside_home=inside_home,force=force,entrusted=entrusted,employee=employee)
            st.session_state.pop("llm_report",None)
            st.success("Case facts saved. Open ‘2 · Check the legal date’ from the left.")

    st.markdown("### Example of collected data")
    raw=sample_case_data()
    st.dataframe(raw,use_container_width=True,hide_index=True)

    st.markdown("### B · Data cleaning")
    st.write("Clean the data in this order so the same case is not counted twice and obvious errors do not mislead the system.")
    cleaned,encoded,median_value,upper_limit=clean_case_data(raw)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Rows collected",len(raw))
    c2.metric("Duplicate rows",int(raw.duplicated().sum()))
    c3.metric("Missing cells",int(raw.isna().sum().sum()))
    c4.metric("Large value flagged","1")

    steps=st.tabs(["1 · Duplicates","2 · Missing values","3 · Outliers","4 · Encode text"])
    with steps[0]:
        st.write("A duplicate is the same record entered more than once. CASE-102 appears twice, so one copy is removed.")
        st.code("data = data.drop_duplicates()",language="python")
        st.dataframe(raw[raw.duplicated(keep=False)],use_container_width=True,hide_index=True)
    with steps[1]:
        st.write("A missing value is an empty cell. An unknown location is labelled ‘Unknown’. A missing property value is filled with the middle value from the available records.")
        st.code("data['location'] = data['location'].fillna('Unknown')\ndata['property_value_inr'] = data['property_value_inr'].fillna(data['property_value_inr'].median())",language="python")
        st.info(f"The example’s missing property value is filled with ₹{median_value:,.0f}.")
    with steps[2]:
        st.write("An outlier is a value far outside the usual range. Here, an unusually large property value is capped at a chosen upper limit instead of deleting the whole case.")
        st.code("upper = data['property_value_inr'].quantile(0.90)\ndata['property_value_inr'] = data['property_value_inr'].clip(upper=upper)",language="python")
        st.info(f"Values above ₹{upper_limit:,.0f} are clipped to that limit in this demonstration.")
    with steps[3]:
        st.write("A machine-learning model needs numbers. Text categories such as ‘theft’ and ‘robbery’ are changed into separate 0-or-1 columns. This is called one-hot encoding.")
        st.code("data = pd.get_dummies(data, columns=['case_type'], dtype=int)",language="python")
        encoded_cols=[c for c in encoded.columns if c.startswith("case_type_")]
        st.dataframe(encoded[["case_id"]+encoded_cols],use_container_width=True,hide_index=True)

    st.markdown("### Before and after cleaning")
    before,after=st.columns(2)
    before.markdown("#### Before")
    before.dataframe(raw,use_container_width=True,hide_index=True)
    after.markdown("#### After")
    after.dataframe(encoded,use_container_width=True,hide_index=True)
    st.caption("This is a teaching example. In a real legal system, every correction must be logged and reviewed rather than silently changing source records.")

elif page==PAGES[2]:
    st.markdown("## Phase 2 · Run the legal-date model")
    st.markdown("""<div class='card'><b>What happens in this phase?</b><br><br>
    The system reads the cleaned case details, finds possible laws and checks which law was being used on the date of the event.<br><br>
    <b>Input:</b> Cleaned case details &nbsp;→&nbsp; <b>Process:</b> Find laws and check their dates &nbsp;→&nbsp; <b>Output:</b> The starting law and information needed for the report.
    </div>""",unsafe_allow_html=True)
    st.markdown("### How it works")
    st.markdown("""<div class='flow'>
    <div class='chip'><b>1 · Input</b><br>Case facts</div><span>→</span>
    <div class='chip'><b>2 · Retrieve</b><br>Possible laws</div><span>→</span>
    <div class='chip'><b>3 · Date rule</b><br>Check start and end dates</div><span>→</span>
    <div class='chip'><b>4 · Verified context</b><br>Selected law + sources</div><span>→</span>
    <div class='chip'><b>5 · LLM</b><br>Draft report</div>
    </div>""",unsafe_allow_html=True)
    ollama_explainer()
    library,retrieved,selected=run_legal_date_model(c)
    st.markdown("### Step 1 · The model reads the case")
    i1,i2,i3=st.columns(3)
    i1.metric("Incident date",c["incident_date"].strftime("%d %b %Y"))
    i2.metric("Place",c["location"])
    i3.metric("Possible topic","Theft")

    st.markdown("### Step 2 · Retrieval finds possible legal records")
    shown=retrieved[["law","full_name","starts_on","ends_on","starting_section","retrieval_matches"]].copy()
    shown.columns=["Law","Full name","Starts on","Ends on","Starting section","Matching words"]
    shown["Ends on"]=shown["Ends on"].apply(lambda value: "Still active" if value is None else value)
    st.dataframe(shown,use_container_width=True,hide_index=True)

    st.markdown("### Step 3 · The exact date rule chooses one period")
    st.code("""matching_law = laws[
    (incident_date >= laws['starts_on']) &
    (laws['ends_on'].isna() | (incident_date <= laws['ends_on']))
]""",language="python")
    st.plotly_chart(timeline(c),use_container_width=True,config={"displayModeBar":False})
    m1,m2,m3=st.columns(3);m1.metric("Incident date",c["incident_date"].strftime("%d %b %Y"));m2.metric("BNS commencement","1 Jul 2024");m3.metric("Starting law","IPC" if a["old"] else "BNS")
    st.success(f"**Model output:** Start with {selected['full_name']} — {selected['starting_section']}.")
    if a["old"]: st.write("The incident is before 1 July 2024, so the model selects the IPC period. A case heard later does not automatically move into the BNS period.")
    else: st.write("The incident is on or after 1 July 2024, so the model selects the BNS period. The exact provision and any special law still require verification.")
    st.markdown("### Why this model is used")
    st.markdown("- **Retrieval** narrows a large collection of laws to possible matches.\n- **The date rule** gives a repeatable answer instead of asking an AI to guess.\n- **The explanation layer** can present the result in simple language and cite its source.\n- **A lawyer still reviews the result** because facts, amendments, exceptions and special laws can change the answer.")
    st.markdown("### Complete hybrid pipeline code")
    st.write("This version shows both parts: the exact date check and the LLM that writes the report.")
    with st.expander("Show date rule + LLM report generator",expanded=False):
        st.code('''from datetime import date
import pandas as pd
from ollama import Client

def generate_legal_report(incident_date, case_description):
    # Part 1: retrieve possible laws from verified legal records.
    laws = pd.DataFrame([
        {
            "law": "IPC",
            "starts_on": date(1862, 1, 1),
            "ends_on": date(2024, 6, 30),
            "section": "Sections 378/379",
            "search_terms": "theft property dishonest taking",
        },
        {
            "law": "BNS",
            "starts_on": date(2024, 7, 1),
            "ends_on": None,
            "section": "Section 303",
            "search_terms": "theft property dishonest taking",
        },
    ])

    case_words = set(case_description.lower().split())
    laws["matching_words"] = laws["search_terms"].apply(
        lambda text: len(case_words.intersection(text.split()))
    )
    retrieved = laws[laws["matching_words"] > 0]
    if retrieved.empty:
        retrieved = laws

    # Part 2: use an exact rule to select the law active on that date.
    date_match = retrieved[
        (incident_date >= retrieved["starts_on"])
        & (
            retrieved["ends_on"].isna()
            | (incident_date <= retrieved["ends_on"])
        )
    ]
    selected = date_match[["law", "section"]].iloc[0]

    # Part 3: give the verified result to the LLM.
    verified_context = f"""
    Incident date: {incident_date}
    Case description: {case_description}
    Selected law: {selected['law']}
    Starting section: {selected['section']}
    """

    client = Client(host="http://localhost:11434")
    response = client.chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": (
                "Write a short educational legal issue report using only the "
                "verified context. Do not change the selected law or invent facts."
            )},
            {"role": "user", "content": verified_context},
        ],
        options={"temperature": 0.1},
    )

    # Part 4: return the report written by the LLM.
    return response.message.content

report = generate_legal_report(
    incident_date=date(2020, 12, 31),
    case_description="Gold jewellery was taken from a house",
)
print(report)
''',language="python")
    st.warning("Continuing offences, saving clauses, procedure, state amendments and special laws require separate review.")

elif page==PAGES[3]:
    st.markdown("## Phase 3 · Evaluate the model")
    st.markdown("""<div class='card'><b>What happens in this phase?</b><br><br>We test whether the system chooses the correct legal period for known dates. We also check whether the generated report contains the required facts, source links and safety warning.<br><br><b>Input:</b> Test cases with known answers &nbsp;→&nbsp; <b>Process:</b> Compare expected and produced answers &nbsp;→&nbsp; <b>Output:</b> Passed checks and problems that need correction.</div>""",unsafe_allow_html=True)

    st.markdown("### A · Test the date-selection rule")
    st.write("These test cases include dates immediately before and after the law-change date. The expected answer is written before the test is run.")
    tests=date_rule_evaluation()
    passed=int((tests["result"]=="Pass").sum())
    total=len(tests)
    accuracy=passed/total
    m1,m2,m3=st.columns(3)
    m1.metric("Tests passed",f"{passed}/{total}")
    m2.metric("Test accuracy",f"{accuracy:.0%}")
    m3.metric("Failed tests",total-passed)
    shown=tests.copy()
    shown.columns=["Test case","Incident date","Expected law","System answer","Result"]
    st.dataframe(shown,use_container_width=True,hide_index=True)
    st.code("""predicted_law = "IPC" if incident_date < date(2024, 7, 1) else "BNS"
passed = predicted_law == expected_law""",language="python")
    st.caption("This score tests only the date rule on five demonstration cases. It is not a claim that the entire legal system is 100% accurate.")

    st.markdown("### B · Check the generated report")
    report=st.session_state.get("llm_report")
    checks=report_quality_checks(report,c,a)
    if checks is None:
        st.info("No local-LLM report has been generated in this session. Generate a report in Phase 4, then return here to evaluate it.")
    else:
        checks["Result"]=checks["passed"].map({True:"Pass",False:"Needs review"})
        st.dataframe(checks[["check","Result"]].rename(columns={"check":"Report check"}),use_container_width=True,hide_index=True)
        report_passed=int(checks["passed"].sum())
        r1,r2=st.columns(2)
        r1.metric("Automatic checks passed",f"{report_passed}/{len(checks)}")
        r2.metric("Checks needing review",len(checks)-report_passed)

    st.markdown("### C · Human review checklist")
    st.markdown("- Does the report describe the case facts correctly?\n- Does it use the law selected by the date rule?\n- Do the links open the official sources?\n- Did the model add any fact, section or judgment that was not supplied?\n- Is uncertainty clearly shown?\n- Does the report avoid deciding guilt or punishment?")
    st.warning("Automatic checks can find missing words or links, but they cannot prove that every legal statement is correct. A qualified human must review the report.")

elif page==PAGES[4]:
    st.markdown("## Phase 4 · Generate the legal issue report")
    st.markdown("""<div class='card'><b>Where is the LLM used?</b><br>The rule system has already selected the legal period. The LLM now turns the verified case facts, selected law, flagged issues and official links into a readable draft report.</div>""",unsafe_allow_html=True)
    st.markdown("### Report-generation flow")
    st.markdown("""<div class='flow'><div class='chip'>Case facts</div><span>+</span><div class='chip'>Verified date result</div><span>+</span><div class='chip'>Official sources</div><span>→</span><div class='chip'><b>LLM</b></div><span>→</span><div class='chip'>Draft report</div></div>""",unsafe_allow_html=True)
    with st.expander("Show the Ollama report-generation code",expanded=False):
        st.code('''from ollama import Client

client = Client(host="http://localhost:11434")
response = client.chat(
    model="llama3.2",
    messages=[
        {"role": "system", "content": (
            "Write an educational legal issue report only from the verified "
            "context. Do not invent facts or change the selected law."
        )},
        {"role": "user", "content": verified_case_context},
    ],
    options={"temperature": 0.1},
)
report = response.message.content
''',language="python")
    model_name=st.text_input("Ollama model",value="llama3.2",help="The model must already be downloaded in Ollama.")
    ollama_host=st.text_input("Ollama address",value="http://localhost:11434")
    st.code("ollama pull llama3.2",language="powershell")
    generate=st.button("Generate report with local Ollama",type="primary",use_container_width=True)
    if generate:
        try:
            with st.spinner("The local LLM is drafting the report from the verified context..."):
                st.session_state.llm_report=generate_llm_report(c,a,model_name,ollama_host)
            st.success("Local LLM report generated. A human legal review is still required.")
        except Exception as exc:
            st.error(f"Could not reach Ollama or run the model: {exc}")
            st.info("Make sure Ollama is running and run `ollama pull llama3.2` once in the VS Code terminal.")
    report=st.session_state.get("llm_report")
    if report:
        st.markdown("### LLM-generated draft")
        st.markdown(report)
        filename=f"llm-legal-report-{c['incident_date'].isoformat()}.md"
    else:
        st.markdown("### Preview without an API call")
        st.caption("This preview uses the fixed template. Start Ollama and press the button above to generate the local-LLM version.")
        report=report_text(c,a);st.markdown(report)
        filename=f"template-legal-report-{c['incident_date'].isoformat()}.md"
    st.download_button("Download report as Markdown",report,file_name=filename,mime="text/markdown",use_container_width=True)
    st.error("Human legal review is mandatory. This report does not decide guilt, sentence or the final applicable provision.")
