import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from feature_lab import (
    animated_visual, assembly_lab, compare_lab, concept_map_lab, detective_lab,
    device_explorer, init_state, memory_simulator, misconception_lab,
    personalized_path, portfolio, render_tutor, teachback_lab,
    troubleshooting_lab, what_if_lab, xray_lab,
)

st.set_page_config(page_title="Computer Fundamentals Explorer", page_icon="🖥️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
:root{--bg:#06111d;--panel:#0d1d2d;--panel2:#12283e;--line:#294960;--text:#eef8ff;--muted:#acc1d1;--cyan:#43d9ff;--green:#5ee5aa;--amber:#ffc867;--pink:#ff86aa}
.stApp{background:radial-gradient(circle at 85% -5%,rgba(67,217,255,.14),transparent 31%),linear-gradient(180deg,#06111d,#091624);color:var(--text);font-family:'DM Sans',sans-serif;font-size:19px}.block-container{max-width:1200px;padding-top:1.7rem;padding-bottom:4rem}h1,h2,h3{font-family:'Space Grotesk',sans-serif!important}.stMarkdown p,.stMarkdown li{font-size:1.24rem!important;line-height:1.76}.stMarkdown ul,.stMarkdown ol{padding-left:1.7rem}.stMarkdown li{padding:.14rem 0}.stMarkdown h2{font-size:2.35rem!important;line-height:1.2}.stMarkdown h3{font-size:1.65rem!important;line-height:1.3}div[data-testid="stCaptionContainer"] p{font-size:1.08rem!important;line-height:1.55}div[data-testid="stAlert"] p{font-size:1.13rem!important;line-height:1.6}label,p[data-testid="stWidgetLabel"]{font-size:1.1rem!important}div[data-testid="stDataFrame"]{font-size:1.06rem}div[role="radiogroup"] label{font-size:1.08rem!important}
.hero{padding:2rem;border:1px solid var(--line);border-radius:26px;background:linear-gradient(135deg,#132b42,#081a2a)}.eyebrow{color:var(--cyan);font-size:.76rem;font-weight:700;letter-spacing:.14em}.hero h1{font-size:clamp(2.25rem,5vw,4.15rem);margin:.35rem 0}.hero p,.card p{color:var(--muted)}
.card{height:100%;padding:1.25rem;border:1px solid var(--line);border-radius:18px;background:linear-gradient(145deg,#12283e,#0a1b2b)}.card h3{font-size:1.42rem!important;line-height:1.28;margin:.7rem 0 .45rem}.card p{font-size:1.08rem;line-height:1.58}.badge{display:inline-grid;place-items:center;min-width:42px;height:42px;padding:0 .6rem;border-radius:12px;background:rgba(67,217,255,.13);color:var(--cyan);font-size:1.08rem;font-weight:700}.lesson-bridge{padding:1.25rem 1.35rem;margin:.25rem 0 1.2rem;border:1px solid rgba(94,229,170,.34);border-radius:18px;background:linear-gradient(135deg,rgba(94,229,170,.09),rgba(67,217,255,.06));font-size:1.08rem;line-height:1.6}.lesson-bridge b{color:var(--green)}.next-step{padding:1.15rem 1.25rem;margin-top:1.6rem;border:1px solid rgba(255,200,103,.35);border-radius:16px;background:rgba(255,200,103,.07);font-size:1.08rem;line-height:1.6}.example{font-size:1.08rem;line-height:1.6}
.machine{display:grid;grid-template-columns:1fr 1.25fr 1fr;gap:1rem;align-items:center;padding:1.25rem;border:1px solid var(--line);border-radius:22px;background:#0b1b2b}.machine-box{padding:1.15rem;text-align:center;border:1px solid var(--line);border-radius:16px;background:#12283e}.machine-box b{display:block;color:var(--cyan);font-size:1.05rem}.machine-arrow{text-align:center;color:var(--amber);font-size:2rem}
.board{position:relative;min-height:380px;border:2px solid #2d6078;border-radius:24px;background:linear-gradient(145deg,#14394a,#0c2936);padding:1rem}.part{position:absolute;padding:.75rem;border:1px solid #4b7890;border-radius:12px;background:#102235;text-align:center;box-shadow:0 8px 18px rgba(0,0,0,.22)}.part b{color:var(--cyan)}
.flow{display:flex;gap:.55rem;align-items:stretch;flex-wrap:wrap;margin:1rem 0}.node{flex:1;min-width:145px;padding:1rem;border:1px solid var(--line);border-radius:16px;background:var(--panel)}.node b{color:var(--cyan)}.arrow{display:grid;place-items:center;color:var(--amber);font-size:1.4rem}.example{padding:1rem 1.1rem;border-left:4px solid var(--amber);border-radius:0 14px 14px 0;background:rgba(255,200,103,.08)}
div[data-testid="stSidebar"]{background:#081522;border-right:1px solid var(--line)}div[data-testid="stMetric"]{border:1px solid var(--line);background:#0d1d2d;padding:1rem;border-radius:16px}.stButton>button{border-radius:12px;border:1px solid #34708b;background:#11364c;color:#eef8ff;font-weight:700}
@media(max-width:760px){.machine{grid-template-columns:1fr}.machine-arrow{transform:rotate(90deg)}.board{min-height:520px}}
</style>
""", unsafe_allow_html=True)

CORE_PAGES=["1 · What is a Computer?","2 · Hardware and Software","3 · Inside the Computer","4 · Storage: HDD vs SSD","5 · Input, Output and Peripherals","6 · Operating System Basics","7 · Data Processing Cycle","8 · Visual Summary","9 · Knowledge Check"]
PAGES=CORE_PAGES
init_state()
page=st.sidebar.radio("Unit 1.2 learning journey",PAGES)
st.sidebar.markdown("---");st.sidebar.markdown("**Unit 1.2 · Computer Fundamentals**");st.sidebar.caption("Every technical term is introduced before it is used.")
step_number=PAGES.index(page)+1
st.sidebar.progress(step_number/len(PAGES));st.sidebar.caption(f"Step {step_number} of {len(PAGES)}")
st.markdown("""<div class='hero'><div class='eyebrow'>UNIT 1.2 · INTERACTIVE ILLUSTRATION</div><h1>Computer Fundamentals</h1><p>Look inside a computer and learn how its physical parts and software work together to receive data, process it, store it and produce a useful result.</p></div>""",unsafe_allow_html=True);st.write("")

BRIDGES={
PAGES[0]:("Starting point","First understand what a computer does before examining the parts that make it work."),
PAGES[1]:("From purpose to parts","Now that you know what a computer does, separate the physical machine from the instructions it follows."),
PAGES[2]:("From two groups to specific components","Hardware is a broad group. This page opens the computer and identifies its most important internal parts."),
PAGES[3]:("A closer look at one internal part","The previous page introduced storage. Now compare the two common ways a computer keeps files for the long term."),
PAGES[4]:("Connecting the computer to people","Internal parts do the work, but input and output devices allow people to communicate with the computer."),
PAGES[5]:("Who coordinates everything?","Hardware and applications cannot cooperate by themselves. The operating system coordinates their work."),
PAGES[6]:("Putting every idea into motion","Now combine input devices, processing, output devices and storage into one repeating cycle."),
PAGES[7]:("The complete picture","Review how every component and software layer contributes to one simple task."),
PAGES[8]:("Check your understanding","Apply the full sequence rather than remembering isolated definitions.")}
bridge_title,bridge_text=BRIDGES.get(page,("Practice and explore","Use the activity to apply the ideas introduced in the core lesson."))

PURPOSE={
PAGES[0]:"Build the big picture: every later component makes sense only when you first know the four jobs a computer performs—input, processing, output and storage.",
PAGES[1]:"Separate the physical machine from the instructions it follows, because a useful computer always requires both.",
PAGES[2]:"Identify the main internal components and understand that each performs a different part of the computer's work.",
PAGES[3]:"Understand how long-term storage differs from temporary memory and why HDDs and SSDs offer different experiences.",
PAGES[4]:"See how people provide data to a computer and receive results from it through connected devices.",
PAGES[5]:"Discover the coordinating software that allows applications and hardware to work together without users controlling every component directly.",
PAGES[6]:"Combine everything learned so far into the repeating sequence followed whenever a computer completes a task.",
PAGES[7]:"Bring all the separate ideas together and trace the contribution of each part during one complete activity.",
PAGES[8]:"Demonstrate understanding by reasoning through the connected system rather than memorizing isolated definitions."}
STORY={
PAGES[0]:"Maya wants to type and save a school assignment. Her computer must accept her typing, process it, show the words and save the document.",
PAGES[1]:"The keyboard and screen are hardware. The writing application is software. Maya needs both to create her assignment.",
PAGES[2]:"While Maya types, RAM holds the open document, the CPU follows typing instructions, storage keeps the saved copy and the motherboard connects the parts.",
PAGES[3]:"When Maya clicks Save, the assignment is kept on an HDD or SSD so it remains available after the computer is turned off.",
PAGES[4]:"Maya uses the keyboard as input, sees words on the monitor as output and may use a printer as another output device.",
PAGES[5]:"The operating system carries Maya's keyboard actions to the writing application and helps the application save the document to storage.",
PAGES[6]:"Her typing is input, arranging the letters is processing, showing the sentence is output and saving the document is storage.",
PAGES[7]:"Maya's finished assignment proves that hardware, software and every processing stage operate as one connected system.",
PAGES[8]:"Use Maya's assignment story whenever you need to remember how the computer's parts and stages connect."}
MISCONCEPTION={
PAGES[0]:"A computer does not think like a person; it follows instructions written for it.",
PAGES[1]:"Software is not a physical object inside the case; it is stored instructions executed by hardware.",
PAGES[2]:"The CPU is important, but it cannot replace RAM, storage or the motherboard.",
PAGES[3]:"Storage and RAM are not the same: storage keeps files long-term, while RAM holds current work temporarily.",
PAGES[4]:"A peripheral is not necessarily optional or unimportant; the term simply describes a connected device that adds a function.",
PAGES[5]:"The operating system is not the same as an everyday application; it manages the environment in which applications run.",
PAGES[6]:"Storage is part of the cycle when a result needs to be kept, but some quick tasks may present output without saving it.",
PAGES[7]:"No single component completes the entire task independently.",
PAGES[8]:"Knowing definitions is not enough; understanding the relationships lets you explain what happens during a real task."}
DETAILS={
PAGES[0]:"""A computer works with many kinds of data: numbers, words, pictures, sound and button presses. It does not automatically know what a user wants; software provides exact instructions for handling that data. The same computer can perform different tasks because it can run different software.

The four basic jobs give us a map for the entire unit. Devices provide **input**, internal components perform **processing**, other devices provide **output**, and storage keeps data for future use.""",
PAGES[1]:"""Hardware includes both internal parts and connected devices. Software includes the operating system and applications. Hardware determines what the machine is physically capable of doing, while software determines which task it performs at a particular moment.

When software asks to display a picture, play sound or save a document, hardware carries out those instructions. Their relationship is continuous rather than a one-time handoff.""",
PAGES[2]:"""A computer contains several internal parts, and each part has a different job:

- **CPU (Central Processing Unit):** The processor that follows instructions, performs calculations and controls the steps needed to complete a task.
- **RAM (Random Access Memory):** The computer's temporary working area. It holds the applications and data currently being used, and its contents normally disappear when the computer is turned off.
- **Storage:** The long-term location for applications, documents, photographs and other files. Stored data remains available after the computer is turned off.
- **Motherboard:** The main circuit board inside the computer. The CPU, RAM, storage connections and other components attach to it so they can exchange data.

These parts work as a group. When you open a saved photograph, storage supplies the file, RAM holds it while it is open, the CPU follows the instructions needed to process it, and the motherboard provides the connections used to move data between the components.

Computer performance depends on balance. A fast CPU can still feel slow when there is too little RAM for current work or when storage takes a long time to supply files.""",
PAGES[3]:"""Long-term storage is measured by how much data it can hold, how quickly it can read or save data, and how reliably it retains that data. Both HDDs and SSDs serve the same basic purpose, but their internal methods differ.

An HDD uses spinning disks and a moving read/write mechanism. An SSD uses electronic memory chips, so it normally opens files faster, operates silently and handles movement better.""",
PAGES[4]:"""Input and output describe the direction in which data moves relative to the computer. A keyboard sends data inward, while a monitor presents data outward. Some devices, such as a touchscreen, work in both directions.

Peripheral devices extend what a computer can do. A camera adds image input, speakers add sound output, and a removable drive adds portable storage.""",
PAGES[5]:"""The operating system starts when the computer boots and remains active while it is used. It decides how applications share processing time and memory, organizes files, controls connected devices and provides the interface through which users work.

Windows, Linux, macOS, Android and iOS are examples of operating systems. They look different, but all perform similar coordinating duties.""",
PAGES[6]:"""The processing cycle can describe a tiny action or a complete activity. Pressing one key creates input, software processes the key, the letter appears as output and the document may later be stored.

The cycle repeats extremely quickly. Output from one cycle can become input to another—for example, a saved photograph can later be opened, edited and saved again.""",
PAGES[7]:"""A useful mental model is to ask four questions: What data enters? Which parts and software handle it? What result appears? Where is it kept? Then identify the role of each component.

This approach is more useful than memorizing definitions because it lets you explain unfamiliar computer activities step by step.""",
PAGES[8]:"""For each question, connect the component to its job. If a file must remain after shutdown, think storage. If data is needed only while an application is open, think RAM. If instructions must be executed, think CPU.

After the quiz, revisit any page whose relationship—not merely its definition—is unclear."""}
def cards(items):
    cols=st.columns(len(items))
    for col,(badge,title,body) in zip(cols,items): col.markdown(f"<div class='card'><span class='badge'>{badge}</span><h3>{title}</h3><p>{body}</p></div>",unsafe_allow_html=True)

def bar(labels,values,title,colors=None):
    colors=colors or ["#43d9ff","#5ee5aa","#ffc867","#ff86aa"]
    fig=go.Figure(go.Bar(x=labels,y=values,marker_color=colors[:len(labels)],text=values,textposition="outside"));fig.update_layout(title=title,height=335,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#0d1d2d",font_color="#eef8ff",margin=dict(l=20,r=20,t=55,b=20),yaxis_title="Illustrative value");return fig

ASSETS=Path(__file__).parent/"assets"
def visual_flow(labels,title):
    n=len(labels);fig=go.Figure(go.Sankey(arrangement="fixed",node=dict(label=labels,pad=28,thickness=28,color=["#184a63","#17614f","#6e5321","#6a2945"][:n],line=dict(color="#55dfff",width=1.2),x=[i/(n-1) if n>1 else .5 for i in range(n)],y=[.5]*n),link=dict(source=list(range(n-1)),target=list(range(1,n)),value=[1]*(n-1),color=["rgba(67,217,255,.35)","rgba(94,229,170,.35)","rgba(255,200,103,.35)"][:n-1])));fig.update_layout(title=title,height=300,paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#eef8ff",size=15),margin=dict(l=25,r=25,t=60,b=20));return fig

if page==PAGES[0]:
    st.header("What is a computer?")
    st.markdown("A **computer is an electronic machine that accepts data, follows instructions, produces results and can save those results for later use.**")
    st.markdown("""A computer can work with **numbers, words, pictures, sound and button presses**. What makes it useful is its ability to follow different instructions for different tasks. The same computer can help someone write a document, watch a video, calculate a total or draw a picture simply by running different software.

Every computer activity can be understood through four basic functions:

1. **Input:** data or a command enters the computer.
2. **Processing:** the computer follows instructions and works on the data.
3. **Output:** the computer presents a result.
4. **Storage:** data or results are kept for later use.

The animated diagram below shows these functions as one connected movement.""")
    animated_visual(page)
    st.subheader("What makes a computer different from a simple machine?")
    cards([("1","Programmable","It can follow different sets of instructions for different tasks."),("2","Fast","It can perform many simple operations in a very short time."),("3","Accurate","It gives consistent results when its data and instructions are correct."),("4","Storage","It can keep data and retrieve it later.")])
    st.markdown("<div class='example'><b>Calculator example:</b> You enter 25 × 4, the computer follows multiplication instructions, displays 100 and may keep the calculation in its history.</div>",unsafe_allow_html=True)

elif page==PAGES[1]:
    st.header("Computer hardware and software")
    st.markdown(DETAILS[page])
    cards([("🔧","Hardware","The physical parts of a computer that can be seen or touched."),("⌘","Software","The instructions and programs that tell the hardware what to do.")])
    st.subheader("Classify an example")
    examples={"Keyboard":"Hardware","Web browser":"Software","Monitor":"Hardware","Photo-editing application":"Software","Memory chip":"Hardware","Operating system":"Software","Printer":"Hardware"}
    item=st.selectbox("Select an item",list(examples));choice=st.radio("Your answer",["Hardware","Software"],horizontal=True,index=None)
    if st.button("Check answer"): (st.success if choice==examples[item] else st.error)(f"{examples[item]} — {'it is a physical part.' if examples[item]=='Hardware' else 'it is a set of instructions.'}")
    st.subheader("They need each other")
    animated_visual(page)
    st.info("Hardware without software has no instructions. Software without hardware has nothing on which to run.")

elif page==PAGES[2]:
    st.header("Inside the computer")
    st.markdown(DETAILS[page])
    animated_visual(page)
    part=st.radio("Select a component to explain",["CPU","RAM","Motherboard","Storage"],horizontal=True)
    details={"CPU":("Central Processing Unit","Carries out instructions, calculations and decisions. It is often described as the computer's processor."),"RAM":("Random Access Memory","Holds data and instructions currently being used. Its contents normally disappear when power is switched off."),"Motherboard":("Main circuit board","Provides connections that allow the CPU, RAM, storage and other parts to communicate."),"Storage":("Long-term data keeping","Keeps applications and files even after the computer is switched off.")}
    st.subheader(details[part][0]);st.write(details[part][1])
    analogy={"CPU":"A cook following steps in a recipe.","RAM":"The kitchen counter holding ingredients currently in use.","Motherboard":"The kitchen layout connecting work areas.","Storage":"The cupboard keeping ingredients for later."}
    st.markdown(f"<div class='example'><b>Simple analogy:</b> {analogy[part]}</div>",unsafe_allow_html=True)
    with st.expander("Practice the internal components",expanded=True):
        xray_lab()
        st.markdown("---")
        assembly_lab()

elif page==PAGES[3]:
    st.header("Storage and HDD vs SSD")
    st.markdown("**Storage keeps applications and files for long-term use, including when the computer is turned off.**")
    st.markdown(DETAILS[page])
    animated_visual(page)
    cards([("HDD","Hard Disk Drive","Stores data on spinning magnetic disks. It usually offers more space for a lower price but contains moving parts."),("SSD","Solid-State Drive","Stores data on electronic memory chips. It has no moving parts and is usually faster and quieter.")])
    feature=st.selectbox("Compare by",["Speed","Noise","Resistance to movement","Cost for the same capacity"])
    values={"Speed":([35,90],"Higher is faster"),"Noise":([80,5],"Higher is noisier"),"Resistance to movement":([35,90],"Higher is more resistant"),"Cost for the same capacity":([35,70],"Higher is more expensive")}
    st.plotly_chart(bar(["HDD","SSD"],values[feature][0],f"{feature} — {values[feature][1]}",["#ffc867","#43d9ff"]),use_container_width=True,config={"displayModeBar":False});st.caption("Values are simplified illustrations, not product specifications.")
    st.dataframe(pd.DataFrame([["How it stores data","Spinning magnetic disks","Electronic memory chips"],["Moving parts","Yes","No"],["Typical strength","Lower cost for large capacity","Fast opening and saving"],["Common use","Large collections and backups","Operating system and everyday applications"]],columns=["Feature","HDD","SSD"]),hide_index=True,use_container_width=True)
    with st.expander("Practice RAM and storage",expanded=True):
        memory_simulator()
        st.markdown("---")
        compare_lab()

elif page==PAGES[4]:
    st.header("Input, output and peripheral devices")
    st.markdown(DETAILS[page])
    animated_visual(page)
    cards([("IN","Input device","Sends data or commands into a computer."),("OUT","Output device","Presents the result produced by a computer."),("↔","Input and output","Some devices both send and receive data."),("+","Peripheral","A device connected to a computer to add a function.")])
    examples={"Keyboard":("Input","Sends letters and commands."),"Mouse":("Input","Sends movement and click actions."),"Microphone":("Input","Sends sound into the computer."),"Monitor":("Output","Displays text, pictures and video."),"Speakers":("Output","Produce sound."),"Printer":("Output","Produces a paper copy."),"Touchscreen":("Both","Displays information and receives touch."),"USB storage drive":("Both","Receives saved data and sends it back when opened.")}
    device=st.selectbox("Explore a device",list(examples));st.info(f"**{examples[device][0]}:** {examples[device][1]}")
    st.markdown("<div class='example'><b>Peripheral does not mean unimportant.</b> It simply means a connected device that adds input, output, storage or communication capability.</div>",unsafe_allow_html=True)
    with st.expander("Practice input and output",expanded=True):
        device_explorer()

elif page==PAGES[5]:
    st.header("Operating system basics")
    st.markdown("An **operating system (OS)** is the main software that manages the computer's hardware and provides a platform on which applications can run.")
    st.markdown(DETAILS[page])
    animated_visual(page)
    os_fig=go.Figure(go.Sunburst(labels=["Computer","User and applications","Operating system","Hardware","Files","Memory","Devices","Processor"],parents=["","Computer","Computer","Computer","Operating system","Operating system","Hardware","Hardware"],values=[8,1,4,3,2,2,1,2],branchvalues="total",marker=dict(colors=["#10283d","#43d9ff","#5ee5aa","#ffc867","#2b8faf","#37a67e","#ce9242","#e0ae50"])));os_fig.update_layout(title="The operating system connects applications with hardware",height=430,paper_bgcolor="rgba(0,0,0,0)",font_color="#eef8ff",margin=dict(l=20,r=20,t=55,b=20));st.plotly_chart(os_fig,use_container_width=True,config={"displayModeBar":False})
    st.subheader("What the operating system helps manage")
    cards([("▣","Applications","Starts, stops and shares resources among programs."),("📁","Files","Creates folders and helps save, find and open files."),("⚙","Hardware","Coordinates the processor, memory, storage and connected devices."),("👤","Users","Supports accounts, passwords and personal settings.")])
    st.markdown("<div class='example'><b>Opening a music file:</b> The OS finds the file, starts the music application, places needed data in memory and sends sound to the speakers.</div>",unsafe_allow_html=True)
    with st.expander("Practice finding a problem",expanded=True):
        troubleshooting_lab()
        st.markdown("---")
        what_if_lab()

elif page==PAGES[6]:
    st.header("The data processing cycle")
    st.markdown("The data processing cycle explains how a computer repeatedly turns input data into useful output and may store the result.")
    st.markdown(DETAILS[page])
    animated_visual(page)
    example=st.selectbox("Choose an everyday example",["Calculator","Taking a photograph","School marks","Online search"])
    cycles={"Calculator":["Enter 25 × 4","Calculate multiplication","Display 100","Keep it in history"],"Taking a photograph":["Camera captures light","Phone processes the image","Screen shows the photo","Photo is saved"],"School marks":["Teacher enters marks","Application totals and averages","Report shows results","Record is saved"],"Online search":["Type search words","Application finds matches","Results appear","Search may be saved"]}
    st.dataframe(pd.DataFrame([cycles[example]],columns=["Input","Processing","Output","Storage"]),hide_index=True,use_container_width=True)
    if st.button("Animate this cycle"):
        progress=st.progress(0);status=st.empty()
        for i,stage in enumerate(["Input","Processing","Output","Storage"],1): status.info(f"{stage}: {cycles[example][i-1]}");progress.progress(i*25);time.sleep(.35)
        status.success("Cycle complete—the stored result can become input for a future cycle.")
    with st.expander("Practice tracing the complete cycle",expanded=True):
        detective_lab()

elif page==PAGES[7]:
    st.header("Visual summary: how the parts work together")
    st.markdown(DETAILS[page])
    animated_visual(page)
    st.subheader("One complete example: writing and saving a sentence")
    st.dataframe(pd.DataFrame([["Keyboard","Provides the letters","Input hardware"],["Operating system","Carries the key actions to the writing application","System software"],["RAM","Holds the open sentence temporarily","Temporary memory"],["CPU","Processes typing and formatting instructions","Processor"],["Monitor","Shows the sentence","Output hardware"],["SSD or HDD","Keeps the saved document","Long-term storage"],["Motherboard","Connects the internal components","Main circuit board"]],columns=["Part","Role in the example","Concept"]),hide_index=True,use_container_width=True)
    st.success("No single part does everything. A computer works because hardware and software cooperate through the data processing cycle.")
    with st.expander("Connect and explain everything you learned",expanded=True):
        concept_map_lab()
        st.markdown("---")
        misconception_lab()
        st.markdown("---")
        teachback_lab()
        st.markdown("---")
        personalized_path()

elif page==PAGES[8]:
    st.header("Unit 1.2 knowledge check")
    st.markdown("Use this final check to connect each computer component with its job and apply the complete data-processing cycle.")
    animated_visual(page)
    questions=[("What is hardware?",["Physical computer parts","Instructions only","Saved information"],0),("Which part carries out instructions?",["CPU","Keyboard","Monitor"],0),("Which part holds current work temporarily?",["RAM","Printer","HDD"],0),("What connects the main internal parts?",["Motherboard","Mouse","Application"],0),("Which normally has no moving parts?",["SSD","HDD","Printer"],0),("Which is an output device?",["Monitor","Keyboard","Microphone"],0),("What is the main role of an operating system?",["Manage hardware and provide a platform for applications","Only save photographs","Only connect a mouse"],0),("Correct processing-cycle order?",["Input → processing → output → storage","Storage → output → input → processing","Processing → storage → input → output"],0)]
    answers=[]
    for i,(question,options,_) in enumerate(questions): answers.append(st.radio(f"{i+1}. {question}",options,index=None,key=f"q{i}"))
    if st.button("Check my answers"):
        if None in answers: st.warning("Answer every question first.")
        else:
            score=sum(answer==options[correct] for answer,(_,options,correct) in zip(answers,questions));st.metric("Score",f"{score} / {len(questions)}")
            (st.success if score>=7 else st.info)("Excellent—you understand the computer fundamentals." if score>=7 else "Review the visual pages and try again.")
    with st.expander("View or download your learning evidence",expanded=False):
        portfolio()

KEY_POINTS={
PAGES[0]:["A computer accepts input data.","It follows stored instructions.","It produces output and can save results."],
PAGES[1]:["Hardware means physical parts.","Software means programs and instructions.","Each needs the other to make the computer useful."],
PAGES[2]:["The CPU follows instructions.","RAM holds current work temporarily.","Storage keeps files long-term.","The motherboard connects internal parts."],
PAGES[3]:["Both HDDs and SSDs keep data after power is off.","HDDs use moving disks.","SSDs use memory chips and are usually faster."],
PAGES[4]:["Input devices send data in.","Output devices present results.","A peripheral adds a function to the computer."],
PAGES[5]:["The operating system is the main coordinating software.","It manages applications, files, memory, devices and users."],
PAGES[6]:["The cycle is input, processing, output and storage.","Stored output can later become new input."],
PAGES[7]:["All parts cooperate to complete a task.","The operating system coordinates hardware and applications."],
PAGES[8]:["The quiz checks understanding of the entire connected story."]}
st.markdown("---");st.subheader("What you should now understand")
for point in KEY_POINTS[page]: st.markdown(f"- {point}")
current=PAGES.index(page)
if current<len(PAGES)-1:
    next_name=PAGES[current+1].split("·",1)[1].strip()
    NEXT_REASON={
    PAGES[0]:"Now that you understand the four basic jobs of a computer, the next step is to learn what makes those jobs possible: hardware—the physical parts—and software—the instructions the computer follows.",
    PAGES[1]:"You can distinguish hardware from software. Next, open the hardware group and learn the jobs of its main internal components.",
    PAGES[2]:"You have met CPU, RAM, motherboard and storage. Next, examine storage more closely and compare HDD with SSD.",
    PAGES[3]:"You know how files remain saved. Next, move outside the computer and learn how data enters and results leave.",
    PAGES[4]:"You understand how people communicate with the machine. Next, discover the operating system that coordinates those devices with applications.",
    PAGES[5]:"You now know what coordinates the system. Next, combine input, processing, output and storage into a complete cycle.",
    PAGES[6]:"You can trace one task through four stages. Next, review how every component supports those stages together.",
    PAGES[7]:"The full system is connected. Next, check whether you can apply that understanding without guidance."}
    next_reason=NEXT_REASON.get(page,"Continue to the next activity and apply another part of the connected computer system.")
    st.markdown(f"<div class='next-step'><b>Next: {next_name}</b><br>{next_reason}</div>",unsafe_allow_html=True)
else:
    st.markdown("<div class='next-step'><b>Unit 1.2 complete:</b><br>You have moved from the purpose of a computer to its parts, software and full data-processing cycle.</div>",unsafe_allow_html=True)

render_tutor(page)
