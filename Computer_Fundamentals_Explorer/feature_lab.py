import base64
import html
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


ASSET_DIR = Path(__file__).parent / "assets"

KNOWLEDGE = {
    "computer": "A computer is an electronic machine that accepts data, follows instructions, produces results and can store data for later use.",
    "hardware": "Hardware means the physical parts of a computer that can be seen or touched, such as a keyboard, monitor, CPU, RAM and storage drive.",
    "software": "Software means programs and instructions that tell computer hardware what to do.",
    "cpu": "The CPU, or Central Processing Unit, follows instructions, performs calculations and controls the steps needed to complete a task.",
    "ram": "RAM is temporary working memory. It holds applications and data currently in use, and normally clears when the computer is turned off.",
    "motherboard": "The motherboard is the main circuit board. It connects the CPU, RAM, storage and other components so they can exchange data.",
    "storage": "Storage keeps applications and files for the long term, including after the computer is turned off.",
    "hdd": "An HDD stores data on spinning magnetic disks. It usually provides large capacity at a lower price, but has moving parts.",
    "ssd": "An SSD stores data on electronic memory chips. It has no moving parts and is usually faster and quieter than an HDD.",
    "input": "Input is data or a command entering a computer through devices such as a keyboard, mouse, microphone or touchscreen.",
    "output": "Output is a result presented by a computer through a monitor, speakers or printer.",
    "peripheral": "A peripheral is a connected device that adds input, output, storage or another function to a computer.",
    "operating system": "The operating system is the main software that coordinates applications, files, memory and hardware devices.",
    "processing cycle": "The data processing cycle is Input → Processing → Output → Storage. The cycle repeats whenever a computer performs a task.",
}


def init_state():
    defaults = {
        "completed_activities": [], "scores": {}, "teachbacks": [], "confidence": {},
        "open_apps": [], "saved_files": ["Family photo.jpg"], "unsaved_work": [],
        "learner_interest": "", "tutor_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, list) else value.copy() if isinstance(value, dict) else value


def complete(name, score=None):
    if name not in st.session_state.completed_activities:
        st.session_state.completed_activities.append(name)
    if score is not None:
        st.session_state.scores[name] = score


def animated_visual(page):
    topic = page.split("·", 1)[-1].strip()
    scenes = {
        "What is a Computer?": ("INPUT", "PROCESSING", "OUTPUT", "STORAGE", "The yellow data packet moves from the keyboard into the computer. The CPU processes it, the monitor shows the result, and the drive saves it."),
        "Hardware and Software": ("USER COMMAND", "SOFTWARE INSTRUCTIONS", "HARDWARE WORKS", "RESULT", "The command moves through the software layer before the physical CPU and monitor carry it out. Hardware and software are both required."),
        "Inside the Computer": ("STORED FILE", "RAM", "CPU", "DISPLAY", "Inside the tower, the stored file reaches RAM, then the CPU. The motherboard paths flash as data travels toward the display."),
        "Storage: HDD vs SSD": ("FILE", "HDD: SPINNING DISK", "SSD: MEMORY CHIPS", "SAVED", "The HDD platter rotates while the SSD chips pulse. Both keep the file after shutdown, but they use different mechanisms."),
        "Input, Output and Peripherals": ("KEYBOARD INPUT", "DATA ENTERS", "COMPUTER", "MONITOR OUTPUT", "A key press lights up, travels into the computer as input, and returns to the monitor as visible output."),
        "Operating System Basics": ("APPLICATION", "OPERATING SYSTEM", "HARDWARE", "RESULT", "The operating system moves the application's request to the correct hardware, then helps return the completed result."),
        "Data Processing Cycle": ("1 INPUT", "2 PROCESS", "3 OUTPUT", "4 STORE", "One data packet completes the four-stage cycle. After storage, the returning dotted path shows that saved data can be used again."),
        "Visual Summary": ("PERSON", "INPUT DEVICE", "CPU + RAM", "SHOW OR SAVE", "The animation joins the whole unit: a person provides input, connected internal parts handle it, and the computer displays or stores the result."),
        "Knowledge Check": ("READ", "CONNECT IDEAS", "CHOOSE", "CHECK", "The moving marker demonstrates the thinking sequence: read, connect the component with its job, choose, and check the answer."),
    }
    one, two, three, four, caption = scenes.get(topic, ("INPUT", "PROCESS", "OUTPUT", "STORAGE", "Data moves through the connected computer system."))
    video_names = {
        "What is a Computer?": "what-is-computer.webm", "Hardware and Software": "hardware-software.webm",
        "Inside the Computer": "inside-computer.webm", "Storage: HDD vs SSD": "hdd-ssd.webm",
        "Input, Output and Peripherals": "input-output.webm", "Operating System Basics": "operating-system.webm",
        "Data Processing Cycle": "processing-cycle.webm", "Visual Summary": "visual-summary.webm",
        "Knowledge Check": "knowledge-check.webm",
    }
    video_path = ASSET_DIR / "videos" / video_names.get(topic, "")
    if video_path.exists():
        has_narration = topic == "What is a Computer?"
        st.video(str(video_path), autoplay=not has_narration, muted=not has_narration, loop=not has_narration)
        if has_narration:
            st.caption("Press Play to hear the cleaned narration. The player starts manually so your browser does not block the audio.")
        st.caption(f"Video caption: {caption} The four explanations are also displayed inside the video at the moment each action occurs.")
        return
    steps = {
        "What is a Computer?": ["A key press enters the computer as input.", "The CPU follows instructions and processes the data.", "The monitor presents the processed result.", "The drive can save the result for later use."],
        "Hardware and Software": ["The user gives a command through physical hardware.", "Software translates the command into instructions.", "The CPU and other hardware carry out those instructions.", "The monitor or printer presents the completed result."],
        "Inside the Computer": ["Storage supplies a saved application or file.", "RAM temporarily holds the data being used now.", "The CPU follows instructions and works on that data.", "The motherboard provides the connections between the parts."],
        "Storage: HDD vs SSD": ["A file is sent to long-term storage.", "An HDD records it on a rotating magnetic disk.", "An SSD records it electronically on memory chips.", "Both keep the saved file after the computer is switched off."],
        "Input, Output and Peripherals": ["The keyboard sends letters into the computer.", "A mouse, microphone or camera can provide other input.", "The computer handles the incoming data.", "The monitor, speakers or printer provide output."],
        "Operating System Basics": ["An application asks to open or save something.", "The operating system receives the request.", "It coordinates memory, storage and connected devices.", "The result returns to the application and the user."],
        "Data Processing Cycle": ["Input: data or a command enters.", "Processing: instructions are followed.", "Output: a useful result is presented.", "Storage: the result is kept and can be used again."],
        "Visual Summary": ["A person begins by providing input.", "Software tells the hardware how to handle it.", "CPU, RAM, storage and motherboard cooperate.", "The finished result is displayed, played, printed or saved."],
        "Knowledge Check": ["First, read what the question is asking.", "Recall the job of each relevant component.", "Choose the answer that matches that job.", "Check the explanation, not only the score."],
    }.get(topic, [one, two, three, four])
    step_html = "".join(f'<span class="cap c{i}">{html.escape(value)}</span>' for i, value in enumerate(steps))
    kind = {
        "What is a Computer?": "flow", "Hardware and Software": "handoff",
        "Inside the Computer": "inspect", "Storage: HDD vs SSD": "drives",
        "Input, Output and Peripherals": "io", "Operating System Basics": "os",
        "Data Processing Cycle": "cycle", "Visual Summary": "summary",
        "Knowledge Check": "quiz",
    }.get(topic, "flow")
    overlays = {
        "flow": '<div class="path"></div><div class="arrow"></div><div class="chevrons">› › › ›</div>',
        "handoff": '<div class="paper">SOFTWARE<br>INSTRUCTIONS</div><div class="handoff-arrow">➜</div><div class="gear">⚙</div>',
        "inspect": '<div class="lens"><i></i></div><div class="scanline"></div>',
        "drives": '<div class="hdd-disc"><i></i></div><div class="ssd-bits"><b></b><b></b><b></b><b></b><b></b><b></b></div>',
        "io": '<div class="io-in">INPUT&nbsp; ➜</div><div class="io-out">➜ &nbsp;OUTPUT</div>',
        "os": '<div class="os-stack"><div>APPLICATION</div><div>OPERATING SYSTEM</div><div>HARDWARE</div></div><div class="os-signal">↓</div>',
        "cycle": '<div class="orbit"><span>➜</span><b>INPUT<br>PROCESS<br>OUTPUT<br>STORE</b></div>',
        "summary": '<div class="ray r1"></div><div class="ray r2"></div><div class="ray r3"></div><div class="summary-core">WORKING<br>TOGETHER</div>',
        "quiz": '<div class="quiz-symbol"><span>?</span><b>✓</b></div>',
    }
    overlay = overlays[kind]
    photo = ASSET_DIR / "realistic_computer_workflow.png"
    if not photo.exists():
        return
    encoded = base64.b64encode(photo.read_bytes()).decode()
    components.html(f"""
    <style>
    body{{margin:0;background:#07121d;color:#eef8ff;font-family:'Segoe UI',Arial,sans-serif}}
    .scene{{position:relative;aspect-ratio:16/8;overflow:hidden;border:1px solid #315c74;border-radius:22px;background:#050d16}}
    .photo{{position:absolute;inset:-2%;width:104%;height:104%;object-fit:cover;animation:camera 12s ease-in-out infinite alternate}}
    .shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(1,8,14,.08),transparent 55%,rgba(1,8,14,.56))}}
    .path{{position:absolute;left:15%;top:65%;width:70%;height:4px;border-top:4px dashed rgba(255,209,102,.8);transform:rotate(-9deg);transform-origin:left;filter:drop-shadow(0 0 7px #ffd166)}}
    .arrow{{position:absolute;left:12%;top:63%;width:82px;height:42px;background:linear-gradient(90deg,#ffd166,#ff9f43);clip-path:polygon(0 31%,68% 31%,68% 0,100% 50%,68% 100%,68% 69%,0 69%);filter:drop-shadow(0 0 11px #ffd166);animation:arrowTravel 12s ease-in-out infinite;z-index:4}}
    .chevrons{{position:absolute;left:21%;top:56%;color:#ffd166;font-size:38px;font-weight:900;letter-spacing:70px;transform:rotate(-9deg);text-shadow:0 0 12px #ffd166;animation:chevron 1.2s ease-in-out infinite;white-space:nowrap}}
    .ring{{position:absolute;border:4px solid #5ee5aa;border-radius:50%;box-shadow:0 0 25px #5ee5aa,inset 0 0 18px rgba(94,229,170,.3);opacity:0;transform:scale(.78);transition:.45s ease}}
    .cpu{{left:40.2%;top:18%;width:10%;aspect-ratio:1}}.ram{{left:49%;top:18%;width:5%;height:22%;border-radius:12px;animation-delay:.8s}}.drive{{left:39%;top:59%;width:17%;height:15%;border-radius:18px;animation-delay:1.6s}}.screen{{left:75%;top:14%;width:21%;height:43%;border-radius:16px;animation-delay:2.2s}}
    .label{{position:absolute;padding:8px 12px;border-radius:10px;background:rgba(4,14,24,.84);border:1px solid rgba(255,255,255,.38);font-size:16px;font-weight:750;box-shadow:0 8px 18px rgba(0,0,0,.35);opacity:.42;transform:scale(.96);transition:.4s ease}}.l1{{left:8%;bottom:22%}}.l2{{left:34%;top:6%}}.l3{{left:54%;top:8%}}.l4{{right:5%;bottom:22%}}
    .scene.s0 .l1,.scene.s1 .l2,.scene.s2 .l3,.scene.s3 .l4{{opacity:1;transform:scale(1.08);border-color:#ffd166;box-shadow:0 0 24px rgba(255,209,102,.48)}}.scene.s0 .cpu,.scene.s1 .ram,.scene.s2 .drive,.scene.s3 .screen{{opacity:1;transform:scale(1.12)}}
    .paper{{position:absolute;left:13%;top:23%;padding:18px;background:#f4f0e5;color:#17212a;font-weight:900;transform:rotate(-5deg);box-shadow:0 12px 30px #000;animation:paperMove 6s ease-in-out infinite}}.handoff-arrow{{position:absolute;left:40%;top:28%;font-size:72px;color:#ffd166;animation:pop 1.5s infinite}}.gear{{position:absolute;left:60%;top:20%;font-size:100px;color:#5ee5aa;animation:spin 5s linear infinite}}
    .lens{{position:absolute;left:36%;top:13%;width:210px;height:210px;border:8px solid #ffd166;border-radius:50%;box-shadow:0 0 0 500px rgba(2,8,14,.48),inset 0 0 25px #ffd166;animation:lensMove 12s ease-in-out infinite}}.lens i{{position:absolute;width:95px;height:15px;background:#ffd166;right:-65px;bottom:-25px;transform:rotate(48deg);border-radius:10px}}.scanline{{position:absolute;left:34%;top:15%;width:28%;height:3px;background:#43d9ff;box-shadow:0 0 18px #43d9ff;animation:scan 2s infinite}}
    .hdd-disc{{position:absolute;left:45%;top:51%;width:125px;height:125px;border:9px solid #ffd166;border-radius:50%;box-shadow:0 0 26px #ffd166;animation:spin 2s linear infinite}}.hdd-disc i{{position:absolute;left:50%;top:0;width:7px;height:50%;background:#ff86aa}}.ssd-bits{{position:absolute;left:32%;top:55%;display:grid;grid-template-columns:repeat(3,28px);gap:9px;padding:14px;border:3px solid #43d9ff;background:rgba(4,14,24,.8)}}.ssd-bits b{{height:24px;background:#43d9ff;animation:pop 1.2s infinite}}.ssd-bits b:nth-child(2n){{animation-delay:.4s}}
    .io-in,.io-out{{position:absolute;font-size:36px;font-weight:900;text-shadow:0 0 14px #000;animation:ioIn 3s infinite}}.io-in{{left:6%;top:45%;color:#ffd166}}.io-out{{right:5%;top:27%;color:#43d9ff;animation-name:ioOut}}
    .os-stack{{position:absolute;left:35%;top:12%;width:30%;display:grid;gap:8px}}.os-stack div{{padding:13px;text-align:center;background:rgba(5,19,31,.92);border:2px solid #43d9ff;font-size:18px;font-weight:900;animation:layer 4.5s infinite}}.os-stack div:nth-child(2){{border-color:#ffd166;animation-delay:.7s}}.os-stack div:nth-child(3){{border-color:#5ee5aa;animation-delay:1.4s}}.os-signal{{position:absolute;left:48%;top:5%;font-size:54px;color:#ffd166;animation:drop 2.2s infinite}}
    .orbit{{position:absolute;left:36%;top:10%;width:270px;height:270px;border:7px dashed #ffd166;border-radius:50%;box-shadow:0 0 25px #ffd166;animation:spin 10s linear infinite}}.orbit span{{position:absolute;right:-14px;top:100px;font-size:54px;color:#ffd166}}.orbit b{{position:absolute;inset:55px;display:grid;place-items:center;text-align:center;color:#fff;font-size:19px;line-height:1.45;animation:spin 10s linear infinite reverse}}
    .ray{{position:absolute;left:49%;top:40%;height:5px;width:38%;background:currentColor;transform-origin:left;box-shadow:0 0 16px currentColor;animation:ray 2.4s infinite}}.r1{{transform:rotate(160deg);color:#ffd166}}.r2{{transform:rotate(210deg);color:#43d9ff;animation-delay:.6s}}.r3{{transform:rotate(5deg);color:#5ee5aa;animation-delay:1.2s}}.summary-core{{position:absolute;left:42%;top:28%;width:150px;height:115px;border-radius:50%;display:grid;place-items:center;text-align:center;background:#0a2638;border:4px solid #5ee5aa;font-weight:900;box-shadow:0 0 30px #5ee5aa;animation:pop 2.4s infinite}}
    .quiz-symbol{{position:absolute;left:43%;top:14%;width:170px;height:170px;border-radius:50%;background:rgba(4,14,24,.88);border:6px solid #ffd166;display:grid;place-items:center;box-shadow:0 0 35px #ffd166}}.quiz-symbol span,.quiz-symbol b{{position:absolute;font-size:110px}}.quiz-symbol span{{color:#ffd166;animation:q 6s infinite}}.quiz-symbol b{{color:#5ee5aa;animation:check 6s infinite}}
    .captions{{position:absolute;left:4%;right:4%;bottom:5%;height:58px;display:grid;place-items:center;padding:0 72px;border-radius:14px;background:rgba(3,10,17,.9);border:1px solid rgba(255,255,255,.28);font-size:21px;font-weight:650;text-align:center;line-height:1.35}}.cap{{position:absolute;opacity:0;transform:translateY(10px);transition:.35s ease}}.cap.on{{opacity:1;transform:translateY(0)}}
    .progress{{position:absolute;left:4%;right:4%;bottom:3.6%;height:4px;background:rgba(255,255,255,.18);border-radius:4px;overflow:hidden}}.progress i{{display:block;height:100%;width:0;background:#ffd166;animation:timeline 12s linear infinite}}.replay{{position:absolute;right:5.3%;bottom:8.2%;z-index:3;border:0;border-radius:50%;width:42px;height:42px;background:#43d9ff;color:#04111c;font-size:19px;font-weight:900;cursor:pointer}}
    @keyframes camera{{from{{transform:scale(1)}}to{{transform:scale(1.045)}}}}@keyframes arrowTravel{{0%,18%{{left:12%;top:63%;transform:rotate(-8deg)}}45%{{left:43%;top:34%;transform:rotate(-18deg)}}72%,100%{{left:80%;top:34%;transform:rotate(0)}}}}@keyframes chevron{{50%{{opacity:.35;transform:rotate(-9deg) translateX(12px)}}}}@keyframes timeline{{to{{width:100%}}}}@keyframes paperMove{{50%{{left:50%;transform:rotate(3deg) scale(.8);opacity:.55}}}}@keyframes spin{{to{{transform:rotate(360deg)}}}}@keyframes pop{{50%{{transform:scale(1.18);filter:drop-shadow(0 0 12px currentColor)}}}}@keyframes lensMove{{0%,20%{{left:34%;top:10%}}35%,55%{{left:45%;top:12%}}70%,100%{{left:37%;top:43%}}}}@keyframes scan{{50%{{top:48%}}}}@keyframes ioIn{{50%{{transform:translateX(230px)}}}}@keyframes ioOut{{50%{{transform:translateX(-210px)}}}}@keyframes layer{{50%{{transform:translateY(8px);box-shadow:0 0 20px currentColor}}}}@keyframes drop{{50%{{transform:translateY(175px)}}}}@keyframes ray{{50%{{width:12%;opacity:.35}}}}@keyframes q{{0%,45%{{opacity:1;transform:scale(1)}}55%,100%{{opacity:0;transform:scale(.4)}}}}@keyframes check{{0%,45%{{opacity:0;transform:scale(.4)}}55%,100%{{opacity:1;transform:scale(1)}}}}
    @media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
    </style><div class="scene s0" id="scene"><img class="photo" src="data:image/png;base64,{encoded}" alt="Semi-realistic animated computer workstation"><div class="shade"></div>{overlay}<div class="ring cpu"></div><div class="ring ram"></div><div class="ring drive"></div><div class="ring screen"></div><div class="label l1">{html.escape(one)}</div><div class="label l2">{html.escape(two)}</div><div class="label l3">{html.escape(three)}</div><div class="label l4">{html.escape(four)}</div><div class="captions">{step_html}</div><button class="replay" id="replay" aria-label="Replay explanation">↻</button><div class="progress"><i id="bar"></i></div></div>
    <script>const caps=[...document.querySelectorAll('.cap')],scene=document.getElementById('scene');let start=Date.now();function tick(){{const elapsed=(Date.now()-start)%12000;const step=Math.min(3,Math.floor(elapsed/3000));scene.className='scene s'+step;caps.forEach((c,i)=>c.classList.toggle('on',i===step));requestAnimationFrame(tick)}}document.getElementById('replay').onclick=()=>{{start=Date.now();const old=document.getElementById('bar');const fresh=old.cloneNode(true);old.replaceWith(fresh)}};tick();</script>
    """, height=610, scrolling=False)
    st.caption(f"Animation caption: {caption}")


def tutor_answer(question, page):
    q = question.lower().strip()
    interest = st.session_state.learner_interest.strip()
    for marker in ["i like ", "i enjoy ", "i am interested in ", "my interest is "]:
        if marker in q:
            interest = question.lower().split(marker, 1)[1].strip(" .!?")
            st.session_state.learner_interest = interest
            return f"I’ll remember that you like {interest}. " + personalized_example("computer", interest)
    if "difference" in q or " vs " in q or "compare" in q:
        if "ram" in q and "storage" in q:
            return "RAM holds current work temporarily; storage keeps applications and files long-term. RAM normally clears at shutdown, while saved storage remains."
        if "hdd" in q and "ssd" in q:
            return "Both keep data long-term. An HDD uses moving magnetic disks; an SSD uses memory chips and is usually faster, quieter and more resistant to movement."
        if "hardware" in q and "software" in q:
            return "Hardware is physical and touchable. Software is the set of programs and instructions executed by that hardware."
    for key, answer in KNOWLEDGE.items():
        if key in q:
            return answer + ("\n\n" + personalized_example(key, interest) if interest else "")
    if "this page" in q or "current" in q:
        return f"You are studying {page.split('·',1)[-1].strip()}. Ask me to explain, compare, give an example, or quiz you on this concept."
    if "quiz" in q:
        return "Try this: A document is open now but has not been saved. Which component temporarily holds the current work—CPU, RAM or storage? Answer: RAM."
    return "I can help with computers, hardware, software, CPU, RAM, motherboard, storage, HDD, SSD, input, output, peripherals, operating systems and the data processing cycle. Please mention one of these concepts."


def personalized_example(concept, interest):
    interest = interest.strip().lower()
    if interest.startswith("i like "):
        interest = interest[7:]
    if "harry potter" in interest or "hogwarts" in interest:
        examples = {
            "computer": "Imagine creating a Hogwarts scene: your keyboard provides the words, the computer follows the editing instructions, the monitor shows the scene, and storage keeps the finished project.",
            "hardware": "For a Harry Potter movie project, the keyboard, monitor and computer are the physical props you can touch—these are hardware.",
            "software": "The video-editing program is like the written spell instructions: it tells the physical computer exactly how to arrange each movie scene.",
            "cpu": "Think of the CPU as the performer following a spell's steps: it executes each instruction needed to play, pause or edit a Hogwarts scene.",
            "ram": "RAM is like an open spellbook on Hermione's desk: it temporarily holds the pages and notes being used in the current scene; closing the work clears that temporary desk space.",
            "storage": "Storage is like the Hogwarts library archive: all eight film files can remain there after the computer is turned off and can be opened again later.",
            "motherboard": "The motherboard is like Hogwarts' moving stairways: it provides the routes that let CPU, RAM and storage exchange data.",
            "hdd": "An HDD is like a rotating archive carousel holding Harry Potter movie files on spinning magnetic disks.",
            "ssd": "An SSD is like instantly summoning the chosen Hogwarts scene from an enchanted shelf—electronic chips retrieve it quickly without a spinning disk.",
            "input": "Typing a character's name, clicking Play or speaking a search request for a Harry Potter movie are all input actions.",
            "output": "The Hogwarts scene appearing on the monitor and its music playing through speakers are output.",
            "operating system": "The operating system works like Professor McGonagall organizing Hogwarts: it coordinates the movie application, memory, storage, screen and speakers.",
            "processing cycle": "Search for a Harry Potter scene: your words are input, the computer finds the match during processing, the scene list is output, and a downloaded copy goes to storage.",
        }
        return "Personalized Harry Potter example: " + examples.get(concept, examples["computer"])
    themes = {
        "gaming": ("game command", "current level", "saved game", "score and graphics"),
        "music": ("play command", "song currently playing", "music library", "sound from the speakers"),
        "sport": ("score entry", "live match data", "season records", "scoreboard result"),
        "cook": ("recipe choice", "recipe currently open", "saved recipe collection", "instructions on the screen"),
        "photo": ("camera click", "photo currently being edited", "photo library", "edited picture"),
        "movie": ("play command", "movie scene currently playing", "saved movie collection", "picture and sound"),
    }
    chosen = next((values for word, values in themes.items() if word in interest), None)
    if chosen:
        command, current, saved, result = chosen
        examples = {
            "input": f"Your {command} enters the computer as input.", "ram": f"RAM temporarily holds the {current}.",
            "storage": f"Storage keeps the {saved} after shutdown.", "output": f"The {result} is output.",
            "cpu": f"The CPU follows the instructions needed to turn your {command} into the {result}.",
            "computer": f"Your {command} is input, the CPU processes it with the {current} in RAM, the {result} is output, and storage keeps the {saved}.",
        }
        return f"Personalized {interest} example: " + examples.get(concept, examples["computer"])
    return f"Personalized example based on {interest}: imagine using a related app—your action is input, CPU and RAM handle the current task, the result is output, and storage keeps the saved work."


def render_tutor(page):
    st.markdown("""<style>section[data-testid="stSidebar"] div[data-testid="stPopover"]{position:fixed!important;left:1rem!important;bottom:1rem!important;width:270px!important;z-index:9999}section[data-testid="stSidebar"] div[data-testid="stPopover"] button{background:#123b52!important;border:1px solid #43d9ff!important;color:white!important;font-weight:700!important}</style>""", unsafe_allow_html=True)
    with st.sidebar.popover("💬 Ask Computer Tutor"):
        st.caption(f"Current context: {page.split('·',1)[-1].strip()}")
        interest = st.text_input("What do you like?", value=st.session_state.learner_interest, key="tutor_interest", placeholder="Music, sports, gaming…")
        if interest != st.session_state.learner_interest:
            st.session_state.learner_interest = interest
        quick = st.selectbox("Quick help", ["Choose…", "Explain this page", "Give me a quiz question", "Compare RAM and storage", "Compare hardware and software"])
        question = st.text_input("Ask a question", key="tutor_question", placeholder="Example: What does RAM do?")
        if st.button("Ask", key="ask_tutor"):
            prompt = question or quick
            answer = tutor_answer(prompt, page)
            st.session_state.tutor_history.append((prompt, answer))
        for prompt, answer in st.session_state.tutor_history[-3:]:
            st.markdown(f"**You:** {prompt}")
            st.info(answer)


def assembly_lab():
    st.subheader("Try it: virtual computer assembly")
    st.write("Place each component in the location that matches its role. This simplified activity teaches relationships rather than real installation procedures.")
    components.html("""
    <style>body{background:#081522;color:#eef8ff;font:17px Arial}.wrap{display:grid;grid-template-columns:1fr 1.4fr;gap:18px}.parts,.board{padding:18px;border-radius:18px;border:1px solid #2e6079;background:#0d2031}.part{padding:12px;margin:10px;background:#164059;border:1px solid #43d9ff;border-radius:10px;cursor:grab}.slot{min-height:52px;padding:10px;margin:10px;border:2px dashed #52768b;border-radius:12px}.ok{border-color:#5ee5aa;background:#123d34}.bad{border-color:#ff7d9c;background:#482333}h3{color:#43d9ff}</style>
    <div class="wrap"><div class="parts"><h3>Drag components</h3><div class="part" draggable="true" id="CPU">CPU</div><div class="part" draggable="true" id="RAM">RAM</div><div class="part" draggable="true" id="SSD">SSD</div></div><div class="board"><h3>Motherboard and computer</h3><div class="slot" data-answer="CPU">Processor socket — follows instructions</div><div class="slot" data-answer="RAM">Memory slots — hold current work</div><div class="slot" data-answer="SSD">Storage connection — keeps files</div><p id="result">Drag each part to its matching location.</p></div></div>
    <script>let dragged='';document.querySelectorAll('.part').forEach(p=>p.ondragstart=()=>dragged=p.id);document.querySelectorAll('.slot').forEach(s=>{s.ondragover=e=>e.preventDefault();s.ondrop=e=>{e.preventDefault();if(dragged===s.dataset.answer){s.className='slot ok';s.innerHTML='<b>'+dragged+' correctly placed ✓</b>';document.getElementById(dragged).style.opacity=.35}else{s.className='slot bad';setTimeout(()=>s.className='slot',700)}}})</script>
    """, height=430)
    if st.button("Record assembly activity"):
        complete("Virtual Computer Assembly", 100); st.success("Assembly practice added to your portfolio.")


def what_if_lab():
    st.subheader("Try it: what happens if?")
    scenario = st.selectbox("Remove or disable a part", ["No CPU", "No RAM", "No storage", "No monitor", "No keyboard", "No operating system"])
    results = {
        "No CPU": ("Computer cannot process instructions or start normally.", "CPU", "Processing stops"),
        "No RAM": ("Computer cannot hold the active instructions and data needed to start normally.", "RAM", "Current workspace missing"),
        "No storage": ("The computer has nowhere to load its saved operating system, applications or files from.", "Storage", "Saved content unavailable"),
        "No monitor": ("The computer may still run, but the user cannot see visual output.", "Output", "No visible result"),
        "No keyboard": ("The computer can run, but the user cannot type through that device.", "Input", "Typing unavailable"),
        "No operating system": ("Hardware is present, but the normal environment for running applications is missing.", "Software", "Applications cannot start normally"),
    }
    message, affected, outcome = results[scenario]
    a,b=st.columns(2);a.metric("Affected concept", affected);b.metric("Main outcome", outcome);st.error(message)
    st.info("This simulator isolates one missing part. Real computers may show different messages depending on their design.")
    if st.button("Record simulation"): complete("What Happens If?", 100);st.success("Simulation added to your portfolio.")


def detective_lab():
    st.subheader("Try it: task-to-component detective")
    task = st.selectbox("Choose a task", ["Open a photograph", "Type and save a sentence", "Print a document", "Play music"])
    answers = {
        "Open a photograph":["Storage","RAM","CPU","Monitor"],
        "Type and save a sentence":["Keyboard","RAM and CPU","Monitor","Storage"],
        "Print a document":["Mouse or keyboard","CPU and software","Printer","Storage keeps original"],
        "Play music":["Storage","RAM and CPU","Speakers","Storage keeps music file"],
    }
    options=["Keyboard","Mouse or keyboard","Storage","RAM","CPU","RAM and CPU","CPU and software","Monitor","Printer","Speakers","Storage keeps original","Storage keeps music file"]
    picks=[st.selectbox(label,options,key=f"detect_{i}") for i,label in enumerate(["1 · Where does it begin?","2 · What handles current work?","3 · Where does the result appear?","4 · Where is it kept?"])]
    if st.button("Check detective sequence"):
        target=answers[task];score=sum(a==b for a,b in zip(picks,target));complete("Component Detective",score*25);st.metric("Correct stages",f"{score} / 4");st.write("Correct sequence:"," → ".join(target))


def memory_simulator():
    st.subheader("Try it: live RAM and storage")
    sizes={"Writing app":18,"Web browser":28,"Music app":16,"Photo editor":34}
    app=st.selectbox("Application",list(sizes))
    c1,c2,c3=st.columns(3)
    if c1.button("Open application") and app not in st.session_state.open_apps: st.session_state.open_apps.append(app)
    if c2.button("Create unsaved work"): st.session_state.unsaved_work.append(f"Work in {app}")
    if c3.button("Save current work") and st.session_state.unsaved_work:
        st.session_state.saved_files.extend(st.session_state.unsaved_work);st.session_state.unsaved_work=[]
    ram=sum(sizes[a] for a in st.session_state.open_apps);a,b,c=st.columns(3);a.metric("RAM in use",f"{ram}%");b.metric("Open applications",len(st.session_state.open_apps));c.metric("Saved files",len(st.session_state.saved_files))
    st.progress(min(ram,100)/100);st.write("Unsaved temporary work:",st.session_state.unsaved_work or "None");st.write("Long-term stored files:",st.session_state.saved_files)
    if st.button("Restart computer"):
        st.session_state.open_apps=[];st.session_state.unsaved_work=[];complete("RAM & Storage Simulator",100);st.warning("RAM and unsaved work cleared. Saved files remain in storage.");st.rerun()


def troubleshooting_lab():
    st.subheader("Try it: troubleshooting mini-lab")
    cases={"Many applications are open and the computer becomes slow.":("RAM","Current working memory may be full."),"A document disappears after closing without saving.":("Unsaved work","It was held temporarily but never written to storage."),"The computer runs but the screen is blank.":("Monitor or display connection","Visual output cannot reach the user."),"Typing produces no letters.":("Keyboard or input connection","The input device may not be sending data."),"The computer cannot find its startup software.":("Storage or operating system","Saved startup files may be missing or unavailable.")}
    symptom=st.selectbox("Observed symptom",list(cases));guess=st.radio("Most likely area",["CPU","RAM","Storage or saved work","Input device","Output device","Operating system"],index=None)
    if st.button("Reveal diagnosis"):
        area,why=cases[symptom];st.success(f"Inspect: {area}. {why}");complete("Troubleshooting Mini-Lab",100)


def xray_lab():
    st.subheader("Try it: component X-ray explorer")
    level=st.slider("Zoom level",1,5,1)
    levels={1:("Complete computer","The case contains and protects the internal parts."),2:("Inside the case","The motherboard is the large main circuit board."),3:("Motherboard","The CPU, RAM and component connections are attached here."),4:("Individual component","Select a component to examine its job."),5:("Data movement","See how components exchange data while completing a task.")}
    st.subheader(f"Level {level} · {levels[level][0]}");st.write(levels[level][1])
    scale=1 + (level-1)*0.13
    components.html(f"""<style>body{{margin:0;background:#081522;color:#eef8ff;font-family:Arial}}.x{{height:230px;display:grid;place-items:center;overflow:hidden;border:1px solid #2e6079;border-radius:18px;background:radial-gradient(circle,#17445b,#071522)}}.board{{position:relative;width:360px;height:170px;border:3px solid #5ee5aa;border-radius:18px;background:#123d34;transform:scale({scale});transition:transform .6s}}.chip{{position:absolute;display:grid;place-items:center;border:2px solid #43d9ff;border-radius:9px;background:#10283b;font-weight:bold;animation:p 2s infinite}}.cpu{{width:75px;height:65px;left:140px;top:48px}}.ram{{width:115px;height:25px;left:220px;top:25px;animation-delay:.5s}}.ssd{{width:105px;height:42px;left:25px;top:105px;animation-delay:1s}}@keyframes p{{50%{{box-shadow:0 0 22px #43d9ff;transform:translateY(-4px)}}}}</style><div class='x'><div class='board'><div class='chip cpu'>CPU</div><div class='chip ram'>RAM</div><div class='chip ssd'>SSD</div></div></div>""",height=240)
    st.caption("Move the zoom slider: the motherboard grows closer while CPU, RAM and SSD pulse one by one to show that they are separate connected components.")
    if level>=4:
        component=st.radio("Inspect",["CPU","RAM","SSD","Motherboard"],horizontal=True);st.info(KNOWLEDGE[component.lower()])
    if level==5: st.write("**Example path:** SSD supplies a photograph → RAM holds it → CPU processes it → monitor presents it.")
    if st.button("Record X-Ray exploration"): complete("X-Ray Component Explorer",100);st.success("Exploration added to your portfolio.")


def compare_lab():
    st.subheader("Try it: before-and-after comparison")
    comparison=st.selectbox("Choose a comparison",["Low RAM vs enough RAM","HDD vs SSD","One application vs many","Unsaved vs saved document"])
    data={"Low RAM vs enough RAM":["Frequent waiting when current workspace fills","More current work can remain ready"],"HDD vs SSD":["Moving disks; usually slower opening","Memory chips; usually faster opening"],"One application vs many":["Lower RAM demand","Higher RAM demand"],"Unsaved vs saved document":["May disappear when closed or restarted","Remains in long-term storage"]}
    a,b=st.columns(2);a.error(f"**Before**\n\n{data[comparison][0]}");b.success(f"**After**\n\n{data[comparison][1]}")
    if st.button("Record comparison"): complete("Before & After Lab",100);st.success("Comparison added to your portfolio.")


def teachback_lab():
    st.subheader("Try it: teach the concept back")
    concept=st.selectbox("Explain a concept",["CPU","RAM","Storage","Motherboard","Operating system","Data processing cycle"])
    response=st.text_area("Explain it in your own words",height=140)
    expected={"CPU":["instruction","process"],"RAM":["temporary","current"],"Storage":["long-term","file"],"Motherboard":["connect","component"],"Operating system":["manage","hardware"],"Data processing cycle":["input","processing","output","storage"]}
    if st.button("Check my explanation"):
        found=[word for word in expected[concept] if word in response.lower()];score=round(len(found)/len(expected[concept])*100);complete("Teach-Back Activity",score);st.metric("Essential ideas included",f"{score}%");st.write("Included:",found or "No essential terms yet");st.write("Try to include:",expected[concept])


def misconception_lab():
    st.subheader("Try it: misconception challenge")
    statements=[("RAM keeps files permanently.",False,"RAM is temporary; storage keeps saved files."),("The CPU follows instructions.",True,"The CPU processes instructions and calculations."),("Software can be touched.",False,"Hardware is physical; software is instructions."),("A touchscreen can be input and output.",True,"It displays information and receives touch."),("The motherboard connects internal components.",True,"It provides their main physical connections.")]
    score=0
    for i,(text,truth,explanation) in enumerate(statements):
        answer=st.radio(text,["True","False"],index=None,key=f"myth_{i}")
        if answer is not None and (answer=="True")==truth: score+=1
        if answer is not None: st.caption(explanation)
    if st.button("Score misconceptions"): complete("Misconception Challenge",score*20);st.metric("Score",f"{score} / {len(statements)}")


def concept_map_lab():
    st.subheader("Try it: connect the concept map")
    mapping={"CPU":"Follows instructions","RAM":"Holds current work temporarily","Storage":"Keeps files long-term","Motherboard":"Connects internal components","Operating system":"Coordinates hardware and applications","Keyboard":"Provides input","Monitor":"Presents output"}
    options=list(mapping.values());score=0
    for item,correct in mapping.items():
        answer=st.selectbox(item,["Choose a connection…"]+options,key=f"map_{item}")
        if answer==correct: score+=1
    if st.button("Check concept map"): complete("Interactive Concept Map",round(score/len(mapping)*100));st.metric("Correct connections",f"{score} / {len(mapping)}")


def device_explorer():
    st.subheader("Try it: explore an everyday device")
    device=st.selectbox("Choose a device",["Smartphone","Laptop","ATM","Smart television","Calculator","Digital watch"])
    examples={"Smartphone":["Touchscreen, microphone, camera","Runs apps and calculations","Screen, sound, vibration","Photos, apps and messages"],"Laptop":["Keyboard, touchpad, microphone","Runs applications","Screen and speakers","Documents and applications"],"ATM":["Card reader, keypad","Checks request","Screen, cash and receipt","Transaction record"],"Smart television":["Remote control, microphone","Runs television apps","Picture and sound","Settings and applications"],"Calculator":["Number keys","Performs calculation","Number display","May keep calculation history"],"Digital watch":["Buttons and sensors","Calculates time and activity","Display and vibration","Settings and activity history"]}
    st.dataframe(pd.DataFrame([examples[device]],columns=["Input","Processing","Output","Storage"]),hide_index=True,use_container_width=True)
    if st.button("Record device exploration"): complete("Everyday Device Explorer",100);st.success("Device exploration added to your portfolio.")


def personalized_path():
    st.subheader("Personalized review")
    interest=st.text_input("What do you enjoy?",value=st.session_state.learner_interest,placeholder="Gaming, music, sports, cooking, photography…")
    confidence={topic:st.select_slider(topic,["Need help","Somewhat clear","Confident"],value="Somewhat clear",key=f"conf_{topic}") for topic in ["Hardware vs software","CPU and RAM","Storage","Input and output","Operating system","Processing cycle"]}
    if st.button("Create my learning path"):
        st.session_state.learner_interest=interest;st.session_state.confidence=confidence
        priority=[k for k,v in confidence.items() if v=="Need help"]+[k for k,v in confidence.items() if v=="Somewhat clear"]
        st.success("Recommended order: "+(" → ".join(priority) if priority else "Complete the challenges and knowledge check."));complete("Personalized Learning Path",100)
        if interest: st.info(personalized_example("ram",interest))


def portfolio():
    st.subheader("Your learning evidence")
    completed=st.session_state.completed_activities
    st.metric("Activities completed",f"{len(completed)} / 13")
    st.progress(min(len(completed)/13,1.0));st.write("Completed:",completed or "No activities recorded yet.")
    scores=pd.DataFrame([{"Activity":k,"Score":v} for k,v in st.session_state.scores.items()])
    if not scores.empty: st.dataframe(scores,hide_index=True,use_container_width=True)
    st.subheader("Reflection")
    reflection=st.text_area("What is the most important thing you learned?")
    if reflection: st.success("Reflection included in this session's learning evidence.")
    report=f"UNIT 1.2 LEARNING PORTFOLIO\n\nCompleted: {', '.join(completed) or 'None'}\nScores: {st.session_state.scores}\nInterest: {st.session_state.learner_interest or 'Not provided'}\nReflection: {reflection or 'Not provided'}"
    st.download_button("Download portfolio",report,file_name="unit_1_2_learning_portfolio.txt")
