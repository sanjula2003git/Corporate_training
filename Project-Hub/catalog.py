"""The curated registry of everything built in this repository.

One entry per top-level folder. Everything the filesystem already knows
(notebooks, app.py, README, data files, cell counts) is discovered at run time
by app.py — this file only holds what the filesystem cannot tell you: what the
project teaches, which model family it uses, and where it is deployed.

deploy values
-------------
live      : claimed and reachable on Streamlit Community Cloud
reserved  : notebook deep-links are wired to `slug`, but nobody has claimed that
            App URL in the deploy dialog yet, so those links are still dead
local     : runs with `streamlit run`, never deployed
external  : deployed somewhere other than Streamlit Cloud
scaffold  : started, not finished
none      : no Streamlit app in this folder (notebooks or web code only)
"""

REPO = "https://github.com/sanjula2003git/Corporate_training"
BRANCH = "main"

# Disciplines
CIVIL = "Civil & Infrastructure"
MECH = "Mechanical"
MANU = "Manufacturing"
POWER = "Electrical & Power"
EMERG = "Healthcare & Emergency"
BIZ = "Business & Commerce"
DATA = "Data Foundations"
SOFT = "Software Engineering"

# Tracks
T_ENG = "Engineering AI series"
T_EMERG = "Emergency-response series"
T_BIZ = "Business-decision series"
T_DATA = "Data foundations"
T_WEB = "Full-stack web track"
T_TOOL = "Classroom tools"

PROJECTS = [
    # ---------------------------------------------------- Engineering AI series
    dict(
        folder="Smart-Construction-DL", title="Building an Intelligent Construction Site",
        blurb="The original ML-vs-DL lesson. One construction site, one question: when is a table "
              "of sensor readings enough, and when do you have to look at the picture?",
        discipline=CIVIL, family="Random Forest vs CNN", track=T_ENG,
        deploy="live", slug="manmanagementdilemma-mtwoqgtdc23e7zb5fbwyp2",
        started="2026-07-22", updated="2026-07-23",
    ),
    dict(
        folder="Predictive-Maintenance-DL", title="Intelligent Predictive Maintenance System",
        blurb="A rotating machine announces its failure twice: once in its numbers, once in its "
              "sound. Two model families, one failure.",
        discipline=MECH, family="Random Forest vs CNN", track=T_ENG,
        deploy="live", slug="corporatetraining-erkyvv54wucab9ku87kxvp",
        started="2026-07-22", updated="2026-07-23",
    ),
    dict(
        folder="CNC-Machining-DL", title="AI-Based CNC Machining Optimization",
        blurb="Speed, feed and depth of cut fight each other. ML predicts surface roughness and "
              "tool life, a CNN reads the finished surface, and an optimiser finds the sweet spot.",
        discipline=MANU, family="ML regression + CNN", track=T_ENG,
        deploy="live", slug="cnc-mc2aeavw96wmttw6zuaa53",
        started="2026-07-22", updated="2026-07-23",
    ),
    dict(
        folder="Bridge-DigitalTwin-DL", title="AI-Based Bridge Digital Twin",
        blurb="Structural health monitoring as a teaching device: condition from sensor readings, "
              "cracks from photographs with Grad-CAM, anomaly detection, remaining-life forecast.",
        discipline=CIVIL, family="ML classification + CNN", track=T_ENG,
        deploy="live", slug="corporatetraining-esurdj9vemazqdgjlfd8wz",
        started="2026-07-22", updated="2026-07-23",
    ),
    dict(
        folder="Sustainable-Manufacturing-DL", title="AI for Sustainable Manufacturing",
        blurb="Energy and carbon on a production line. A tuned quadratic load term is what gives "
              "the optimise page a real answer, and the thermal frames defeat any mean threshold.",
        discipline=MANU, family="ML regression + CNN", track=T_ENG,
        deploy="reserved", slug="sustainable-manufacturing",
        started="2026-07-31", updated="2026-07-31",
    ),
    dict(
        folder="Building-Energy-DL", title="AI for Building Energy Optimization",
        blurb="HVAC and comfort in a commercial building. One fixed-damper choice is what makes "
              "the business case land, which is the whole lesson.",
        discipline=CIVIL, family="ML regression + CNN", track=T_ENG,
        deploy="reserved", slug="building-energy-dl",
        started="2026-07-31", updated="2026-08-10",
    ),
    dict(
        folder="Traffic-Signal-DL", title="AI for Traffic Signal Optimization",
        blurb="HCM delay and Webster timing behind an adaptive-versus-fixed benchmark, with a wall "
              "of CCTV feeds for the vision half.",
        discipline=CIVIL, family="ML regression + CNN", track=T_ENG,
        deploy="live", slug="traffic-signal-uyfomtzurrptqrg3pkd6gu",
        started="2026-07-31", updated="2026-08-10",
    ),
    dict(
        folder="Machine-Anomaly-DL", title="Unusual Machine Behaviour Detection",
        blurb="The unsupervised counterpart to predictive maintenance: an autoencoder that has only "
              "ever seen healthy machines still flags a fault nobody showed it.",
        discipline=MECH, family="Autoencoder (unsupervised)", track=T_ENG,
        deploy="live", slug="machine-anomaly-fhclwbacmwj6jorfvdwykv",
        note="URL read from the notebook rather than from a deploy record. Streamlit "
             "answers every slug with a 303 to its login page, real or not, so whether "
             "this one is public can only be checked in a logged-out browser.",
        started="2026-07-31", updated="2026-08-10",
    ),
    dict(
        folder="Cutting-Tool-Recommender-DL", title="AI Cutting Tool Recommendation System",
        blurb="Which insert for this job? A recommendation problem dressed as a machining problem, "
              "in the same five-part-per-step layout as the rest of the series.",
        discipline=MANU, family="MLP recommender", track=T_ENG,
        deploy="reserved", slug="cutting-tool-recommender",
        started="2026-07-31", updated="2026-07-31",
    ),
    dict(
        folder="Transformer-Maintenance-DL", title="AI for Transformer Maintenance Decision Support",
        blurb="A thermal model, the IEEE ageing factor, dissolved-gas signatures and Duval zones "
              "roll into one health index that decides what maintenance happens next.",
        discipline=POWER, family="ML classification + health index", track=T_ENG,
        deploy="reserved", slug="transformer-maintenance-dl",
        started="2026-07-31", updated="2026-07-31",
    ),
    dict(
        folder="Transformer-HotSpot-AI", title="Transformer Hot-Spot Temperature Prediction",
        blurb="IEEE C57.91 hot-spot regression across 31 pages. The physics is what stops the "
              "problem being trivial, and four confident prose claims did not survive the data.",
        discipline=POWER, family="ML regression", track=T_ENG,
        deploy="reserved", slug="transformer-hotspot-ai",
        started="2026-07-31", updated="2026-07-31",
    ),
    dict(
        folder="Load-Forecasting-AI", title="AI for Electricity Load Forecasting",
        blurb="Short-term load forecasting for a feeder. Two confounds in the simulator reversed "
              "the conclusions before they were found; the 23:00 forecast gate is deliberate.",
        discipline=POWER, family="ML time-series regression", track=T_ENG,
        deploy="live", slug="loadforecasting-bnjvsvyuey3uojy32qeeq2",
        started="2026-07-31", updated="2026-07-31",
    ),
    dict(
        folder="Power-Source-Selection-AI", title="AI for Power Source Selection",
        blurb="A microgrid dispatch problem: tariff, solar profile, battery constants and a "
              "dynamic-programming optimiser that the app and the notebook share exactly.",
        discipline=POWER, family="Optimisation + ML", track=T_ENG,
        deploy="live", slug="power-source-selection-vxsrmxenrzt5gbawomj3tc",
        started="2026-07-31", updated="2026-08-10",
    ),
    dict(
        folder="Pavement-Life-Prediction-AI", title="AI for Pavement Remaining Service Life",
        blurb="How many years of service does this pavement have left? The crack-density split and "
              "the narrowed hidden variation are what make traffic and thickness matter at all.",
        discipline=CIVIL, family="ML regression", track=T_ENG,
        deploy="live", slug="pavementlifeprediction-3veds8kg3jnsxvydcparpw",
        note="Deployed private on 2026-07-31 — students hit a sign-in wall until Sharing is set to public.",
        started="2026-07-31", updated="2026-07-31",
    ),
    dict(
        folder="Metro-Evacuation-Flood-LSTM", title="Metro Evacuation Flood Forecasting",
        blurb="Water depth on two underground evacuation routes five minutes ahead, then a "
              "recommendation of the safer exit. Ten one-minute readings in, one depth out.",
        discipline=CIVIL, family="LSTM", track=T_ENG,
        deploy="reserved", slug="metro-evacuation-flood",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Dam-Flood-Water-Security-DL", title="Dam Flood Protection and Water Security",
        blurb="An MLP predicts reservoir level six hours after a forecast storm; a separate, fully "
              "transparent layer proposes a pre-release and caps it by downstream river condition.",
        discipline=CIVIL, family="MLP + decision layer", track=T_ENG,
        deploy="reserved", slug="dam-flood-water-security",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Urban-Road-Flood-GNN", title="Urban Road Flood-Risk Prediction with a GNN",
        blurb="Roads are nodes, connections are edges, and a two-layer graph convolutional network "
              "predicts Low, Medium or High risk before ranking the likely flooding order.",
        discipline=CIVIL, family="Graph neural network", track=T_ENG,
        deploy="reserved", slug="urban-road-flood-gnn",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Rainwater-Harvesting-System-Recommender", title="Rainwater Harvesting Recommender",
        blurb="A daily water-balance simulator makes the training targets, an MLP surrogate "
              "estimates useful annual supply, and the recommended system type stays interpretable.",
        discipline=CIVIL, family="MLP surrogate + optimisation", track=T_ENG,
        deploy="reserved", slug="rainwater-harvesting-recommender",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Retaining-Wall-Type-Recommender", title="Retaining Wall Type Recommendation",
        blurb="Wall type from site conditions, with a cost optimisation behind the recommendation "
              "so the choice can be defended in numbers.",
        discipline=CIVIL, family="MLP + cost optimisation", track=T_ENG,
        deploy="reserved", slug="retaining-wall-recommender",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Road-Maintenance-Priority-Optimizer", title="Road Maintenance Priority Optimizer",
        blurb="An MLP predicts the benefit of maintaining each road; an exact 0/1 knapsack picks "
              "the highest-benefit programme the budget can actually afford.",
        discipline=CIVIL, family="MLP + knapsack optimisation", track=T_ENG,
        deploy="reserved", slug="road-maintenance-priority",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Tower-Crane-Placement-NN-Optimization", title="Tower Crane Placement Optimization",
        blurb="An MLP learns the exact cost surface, a genetic algorithm searches the surrogate, "
              "and the winners are rechecked against exact reach, obstacle and safety-zone maths.",
        discipline=CIVIL, family="NN surrogate + genetic algorithm", track=T_ENG,
        deploy="reserved", slug="tower-crane-placement",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Engine-Operating-Condition-MLP", title="Engine Operating Condition Classification",
        blurb="Seven live sensor readings, one compact MLP, five verdicts: Normal, High Load, "
              "Overheating, Inefficient Operation, Abnormal.",
        discipline=MECH, family="MLP (tabular)", track=T_ENG,
        deploy="reserved", slug="engine-operating-condition",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Gearbox-Vibration-Prediction-1D-CNN", title="Predictive Gearbox Vibration Control",
        blurb="A 1D CNN pulls features out of the vibration waveform, fuses them with RPM, torque, "
              "temperature and motor current, and predicts vibration 30 seconds ahead.",
        discipline=MECH, family="1D CNN + sensor fusion", track=T_ENG,
        deploy="reserved", slug="gearbox-vibration-prediction",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Pump-Cavitation-Audio-DL", title="Pump Cavitation Detection from Sound",
        blurb="Four seconds of pump audio becomes a log-Mel spectrogram, and a 2D CNN calls it "
              "Normal, Mild or Severe cavitation. Sound treated as an image.",
        discipline=MECH, family="2D CNN on spectrograms", track=T_ENG,
        deploy="reserved", slug="pump-cavitation-audio",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Power-Line-Fault-Location-1D-CNN", title="Power-Line Fault Section Identification",
        blurb="A 500x2 voltage and current record goes in; the 5 km section of a 20 km line that "
              "the crew should inspect comes out.",
        discipline=POWER, family="1D CNN", track=T_ENG,
        deploy="reserved", slug="power-line-fault-location",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Generative-Bracket-VAE-DL", title="Generative Design of Lightweight Brackets",
        blurb="A variational autoencoder learns 64x64 bracket silhouettes and samples new ones. "
              "Candidates are screened for mounting regions and connected material, then ranked.",
        discipline=MECH, family="Variational autoencoder", track=T_ENG,
        deploy="reserved", slug="generative-bracket-vae",
        started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="CoolBench-AI", title="CoolBench — Heat Emergency Station",
        blurb="A cooling bench at a sports ground on a hot day: a heat model, competing "
              "controllers, and which one you would trust with a collapsed runner.",
        discipline=EMERG, family="Control + policy search", track=T_ENG,
        deploy="reserved", slug="coolbench", started="2026-08-17", updated="2026-08-17",
    ),
    dict(
        folder="Self-Healing-Grid-AI", title="Self-Healing Grid (in progress)",
        blurb="The Northgate 11 kV network with a backward/forward sweep and a restoration search. "
              "Scaffolding and story stages exist; the notebook and app do not yet.",
        discipline=POWER, family="Network analysis + search", track=T_ENG,
        deploy="scaffold", started="2026-08-10", updated="2026-08-10",
    ),
    dict(
        folder="Adaptive-Evacuation-DL", title="Adaptive Evacuation (in progress)",
        blurb="Scaffold and notebook builder only — the next civil-engineering entry in the series.",
        discipline=CIVIL, family="TBD", track=T_ENG,
        deploy="scaffold", started="2026-08-10", updated="2026-08-10",
    ),

    # ------------------------------------------------- Emergency-response series
    dict(
        folder="CPR-Guardian-AI", title="AI CPR Guardian",
        blurb="A wall unit that coaches an untrained bystander through chest compressions. The "
              "peak-versus-stroke fatigue finding is the heart of it, and the shock-authority "
              "boundary does not move.",
        discipline=EMERG, family="Signal processing + coaching logic", track=T_EMERG,
        deploy="reserved", slug="cpr-guardian-ai", started="2026-08-11", updated="2026-08-18",
    ),
    dict(
        folder="Roadside-Beacon-AI", title="The Golden Minutes — Roadside Beacon",
        blurb="Crash detection plus bystander coaching in the four minutes before an ambulance "
              "arrives. Four simulator fixes stopped every model winning, and the CNN result "
              "overturned the prose that had been written around it.",
        discipline=EMERG, family="Sensor classification + CNN", track=T_EMERG,
        deploy="reserved", slug="roadside-beacon",
        started="2026-08-13", updated="2026-08-18",
    ),
    dict(
        folder="Hospital-Alarm-Fatigue-AI", title="Hospital Alarm-Fatigue Manager",
        blurb="About allocating limited human attention, not about predicting patients. Plain "
              "English throughout, and the only app here whose requirements deliberately omit "
              "TensorFlow.",
        discipline=EMERG, family="Ranking + attention allocation", track=T_EMERG,
        deploy="reserved", slug="hospital-alarm-fatigue",
        started="2026-08-10", updated="2026-08-18",
    ),
    dict(
        folder="Emergency-Cabinet-AI", title="One Door Opens — Intelligent Emergency Cabinet",
        blurb="Seven locked compartments and one decision under uncertainty: which door opens. A "
              "per-item cost table makes the trade-off explicit instead of implied.",
        discipline=EMERG, family="Decision under uncertainty", track=T_EMERG,
        deploy="reserved", slug="emergency-cabinet-ai", started="2026-08-16", updated="2026-08-18",
    ),
    dict(
        folder="Guardian-Road", title="Guardian Road — a shield around a fallen rider",
        blurb="Preventing the second collision after a rider goes down in a live lane: detection, "
              "warning geometry, and how much time there actually is.",
        discipline=EMERG, family="Detection + warning logic", track=T_EMERG,
        deploy="reserved", slug="guardian-road", started="2026-08-16", updated="2026-08-17",
    ),
    dict(
        folder="RescueGrid", title="RescueGrid — first-aid coordination mat",
        blurb="Organising helpers, equipment and responder access in a crowded emergency scene. "
              "The grid itself is the interface.",
        discipline=EMERG, family="Allocation + layout logic", track=T_EMERG,
        deploy="reserved", slug="rescuegrid", started="2026-08-17", updated="2026-08-17",
    ),

    # -------------------------------------------------- Business-decision series
    dict(
        folder="Bakery-Rescue-AI", title="Sell It, Share It, Don't Waste It",
        blurb="Demand forecasting, inventory and marginal costing for a bakery, aimed at B.Com and "
              "M.Com students. Every markdown decision is shown in money.",
        discipline=BIZ, family="Forecasting + marginal costing", track=T_BIZ,
        deploy="reserved", slug="bakery-rescue-ai", started="2026-08-17", updated="2026-08-17",
    ),
    dict(
        folder="Complaint-Rescue-AI", title="From Complaint to Correction",
        blurb="A complaint arrives as free text and leaves as a routed, prioritised, costed action.",
        discipline=BIZ, family="Text classification + routing", track=T_BIZ,
        deploy="reserved", slug="complaint-rescue-ai", started="2026-08-17", updated="2026-08-17",
    ),
    dict(
        folder="Invoice-Guardian-AI", title="Before We Pay Twice — Invoice Guardian",
        blurb="Duplicate-payment detection over an accounts-payable ledger: matching rules first, "
              "then the model, then what each false positive actually costs.",
        discipline=BIZ, family="Matching rules + classification", track=T_BIZ,
        deploy="reserved", slug="invoice-guardian-ai", started="2026-08-17", updated="2026-08-17",
    ),

    # --------------------------------------------------------- Data foundations
    dict(
        folder="Pandas-Student-Basics", title="Pandas Basics — Student Data",
        blurb="The smallest interesting table there is: three columns and a class of students. The "
              "extremes dial is what makes the median-versus-mean difference visible.",
        discipline=DATA, family="pandas only (no ML)", track=T_DATA,
        deploy="reserved", slug="pandas-student-basics", started="2026-08-11", updated="2026-08-18",
    ),
    dict(
        folder="Pandas-Ride-Normal-Basics", title="Pandas Basics — Normally Distributed Ride Data",
        blurb="The symmetric-data counterpart to the student notebook, with a z-score review in "
              "place of the IQR filter so both outlier ideas get taught.",
        discipline=DATA, family="pandas only (no ML)", track=T_DATA,
        deploy="reserved", slug="pandas-ride-normal-basics", started="2026-08-17", updated="2026-08-18",
    ),
    dict(
        folder="machine algorithms", title="Classic ML Algorithms — notebook set",
        blurb="Nine standalone notebooks, one per algorithm: linear and logistic regression, "
              "decision trees, random forest, SVM, KNN, naive Bayes, k-means, and an interactive "
              "regression visualiser.",
        discipline=DATA, family="Nine classic algorithms", track=T_DATA,
        deploy="none", started="2026-08-10", updated="2026-08-10",
    ),

    # ----------------------------------------------------- Full-stack web track
    dict(
        folder="01-HTML-Version", title="Stage 1 — Plain HTML",
        blurb="The training portal as nothing but HTML. Seven pages, no styling, no logic, so "
              "every later layer can be seen arriving.",
        discipline=SOFT, family="HTML", track=T_WEB, deploy="none",
        started="2026-06-03", updated="2026-06-03",
    ),
    dict(
        folder="02-CSS-Styled-Version", title="Stage 2 — HTML + CSS",
        blurb="The same seven pages and one stylesheet. The only thing that changed is appearance, "
              "which is the point.",
        discipline=SOFT, family="HTML + CSS", track=T_WEB, deploy="none",
        started="2026-06-03", updated="2026-06-03",
    ),
    dict(
        folder="03-React-Version", title="Stage 3 — React",
        blurb="The portal rebuilt in React and Vite: components, state and routing replace seven "
              "duplicated HTML files.",
        discipline=SOFT, family="React + Vite", track=T_WEB, deploy="none",
        started="2026-06-03", updated="2026-06-08",
    ),
    dict(
        folder="04-Backend-Python", title="Stage 4 — Python backend",
        blurb="FastAPI with in-memory data and authentication. The first stage where data outlives "
              "the page.",
        discipline=SOFT, family="FastAPI", track=T_WEB, deploy="none",
        started="2026-06-05", updated="2026-06-05",
    ),
    dict(
        folder="05-Backend-Database", title="Stage 5 — Backend + database",
        blurb="SQLite behind the same FastAPI routes, plus a small viewer script so the database "
              "stops being a black box.",
        discipline=SOFT, family="FastAPI + SQLite", track=T_WEB, deploy="none",
        started="2026-06-05", updated="2026-07-06",
    ),
    dict(
        folder="06-Fullstack-Connected", title="Stage 6 — Full-stack connected",
        blurb="React talks to FastAPI talks to SQLite, with role-based portals for admin, trainer "
              "and student.",
        discipline=SOFT, family="React + FastAPI + SQLite", track=T_WEB, deploy="none",
        started="2026-06-05", updated="2026-06-05",
    ),
    dict(
        folder="07-Backend-AI-Chat", title="Stage 7 — AI chat backend",
        blurb="An LLM endpoint added to the same backend, with a mock fallback so the app still "
              "runs without an API key.",
        discipline=SOFT, family="FastAPI + LLM", track=T_WEB, deploy="none",
        started="2026-06-05", updated="2026-06-05",
    ),
    dict(
        folder="08-Fullstack-AI-Chat", title="Stage 8 — AI chat frontend",
        blurb="The chat interface wired to stage 7 — the finished shape of the eight-stage build.",
        discipline=SOFT, family="React + FastAPI + LLM", track=T_WEB, deploy="none",
        started="2026-06-05", updated="2026-06-05",
    ),
    dict(
        folder="corporate_ai_version", title="Corporate Training Portal — deployed",
        blurb="The eight stages finished and actually deployed: React on Vercel, FastAPI on Render, "
              "with Azure, GCP and Supabase deployment guides beside it.",
        discipline=SOFT, family="React + FastAPI, deployed", track=T_WEB,
        deploy="external", live="https://corporate-ai-version.vercel.app",
        note="Backend: https://corporate-ai-backend.onrender.com. Render's free tier re-seeds "
             "SQLite on every restart, so data created live does not survive a redeploy.",
        started="2026-06-25", updated="2026-08-17",
    ),

    # ------------------------------------------------------------ Classroom tools
    dict(
        folder="qp-reveal-puzzle", title="Python Question Bank — Reveal Puzzle",
        blurb="A React app recreating the obfuscated question-paper slides, with an eye and "
              "Ctrl+R reveal mechanic for classroom use.",
        discipline=SOFT, family="React + Vite + Electron", track=T_TOOL, deploy="none",
        started="2026-08-13", updated="2026-08-13",
    ),
    dict(
        folder="qp-spin-3parts", title="Spin Reveal — 3 parts",
        blurb="A standalone spinning-question slide with a student setup screen and seeded "
              "question and dataset selection.",
        discipline=SOFT, family="Vanilla HTML/CSS/JS", track=T_TOOL, deploy="none",
        started="2026-08-05", updated="2026-08-05",
    ),
]

BY_FOLDER = {p["folder"]: p for p in PROJECTS}

TRACK_ORDER = [T_ENG, T_EMERG, T_BIZ, T_DATA, T_WEB, T_TOOL]

TRACK_BLURB = {
    T_ENG: "One engineering problem per project, taught the same way every time: the site, the "
           "engineering challenge, where AI enters, a technical illustration, and what it means. "
           "Most pair a Colab notebook with a Streamlit companion that illustrates every stage.",
    T_EMERG: "Projects where the cost of a wrong answer is a person. The modelling is deliberately "
             "modest; the decision boundaries, and what the system is not allowed to do, carry the "
             "lesson.",
    T_BIZ: "Commerce and management students, same method: a decision that costs money, made "
           "visible in money, with the model as one input rather than the answer.",
    T_DATA: "Before any model: what a table is, what a mean hides, what an outlier does. The pandas "
            "notebooks use no machine learning at all.",
    T_WEB: "The same training portal rebuilt eight times, each stage adding exactly one layer, "
           "ending in a real deployment students can visit.",
    T_TOOL: "Small things built to run in a classroom rather than to teach a syllabus.",
}

DEPLOY_LABEL = {
    "live": "Live on Streamlit Cloud",
    "reserved": "Slug wired, not yet claimed",
    "local": "Runs locally",
    "external": "Deployed (Vercel + Render)",
    "scaffold": "In progress",
    "none": "No Streamlit app",
}

# Table columns are fighting for width, so the status also has a short form. The
# long label stays on the cards and in the legend under each table.
DEPLOY_SHORT = {
    "live": "Live",
    "external": "Live (external)",
    "reserved": "Wired",
    "local": "Local",
    "scaffold": "In progress",
    "none": "No app",
}

# Six statuses need six distinguishable hues: rendering the donut with two
# greens (live / external) and two greys (scaffold / none) made half the legend
# unreadable.
DEPLOY_COLOR = {
    "live": "#3fb950",      # green
    "external": "#a371f7",  # purple — deployed, but not on Streamlit Cloud
    "reserved": "#d29922",  # amber
    "local": "#58a6ff",     # blue
    "scaffold": "#db6d28",  # orange
    "none": "#6e7681",      # grey
}


def live_url(project):
    """The URL worth linking to, or an empty string when nothing is reachable."""
    if project.get("live"):
        return project["live"]
    if project.get("deploy") == "live" and project.get("slug"):
        return f"https://{project['slug']}.streamlit.app"
    return ""
