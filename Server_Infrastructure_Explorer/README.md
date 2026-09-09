# Server Infrastructure Explorer · Unit 5.1

13 lesson pages followed by one interactive 3D explorer. Each lesson contains explanations, a process diagram, an example, a misconception, two practice questions and a topic-specific tutor.

## Start on this computer

Double-click **Start Explorer.bat**, then open http://localhost:8501. Keep the terminal running while using the app. If the app is already running, open the address directly.

On another computer with Python 3.11 or later:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m streamlit run app.py --server.address localhost
```

## Explore the model

- Drag the model to rotate; right-drag to pan; scroll or pinch to zoom. Wheel zoom is stronger and follows the pointer, so point at the component you want to inspect.
- Hover a physical part or topic button to highlight it and read its purpose.
- Click a part, label or topic button to open its matching tutor.
- **Focus selected part** zooms into the selected component; **Full setup** resets the view.
- **Labels** switches all annotations on or off.
- Rotation is manual only: drag to view any side, including the underside. Motion stops when you release the pointer.
- **Full screen** expands the 3D viewer. Press **Esc** or **Exit full screen** to return.

The single scene includes rack, blade and tower forms, a detailed cutaway server, client/network examples for server purpose, and a conceptual architecture board. These are 13 topics, not 13 interchangeable hardware parts. Sizes are illustrative, not manufacturing dimensions. Labels are interactive overlays; the embedded Blender export's baked annotations are hidden.

## Tutor and preferences

A floating chat button on every lesson and the 3D explorer opens a spacious dedicated AI Tutor page. The selected topic and conversation carry across; a return button takes you back. Chat follows the selected component, with shared recent conversation and preferences across pages. Local retrieval covers multiple topics, including relationships such as blade and tower server connections.

Enter your Groq API key directly above the chatbot and click **Activate personalized tutor**, or use **AI connection** in the sidebar. Alternatively configure `GROQ_API_KEY` in the server environment or `.streamlit/secrets.toml` (see the example). Do not commit credentials. The default model is `openai/gpt-oss-120b`, configurable with `GROQ_MODEL`.

With **Search the web for every question** enabled (the default), each answer requests a Groq Compound web lookup restricted to relevant vendor and standards domains, alongside the saved knowledge. The app reports unconfirmed or failed searches honestly. Disable this option to use Groq with saved material only. Without a key, chat shows an explicit connection requirement. Saved notes remain available under Collected web knowledge.

Groq receives questions, recent conversation, retrieved notes and learning preferences. Compound additionally performs web searches; it is instructed to search technical terms only. Provider quotas apply: free access is limited, shared keys share allowances, and web lookup may have separate limits or charges. Two requests per process can run concurrently; busy or rate-limited requests show an explanation and fall back to local knowledge.

Set interests, unwanted examples, language and detail in **Your learning preferences**, or state them in chat. When you say you did not understand, the tutor is instructed to change its explanation and use a different example. Difficult topics and quiz mistakes are tracked to support follow-up teaching.

**Saved learner profile** optionally saves preferences, chat, difficult topics and lesson completion in `runtime/learners.sqlite3`. Keep the generated recovery code private: anyone holding it can restore that profile. Resume with that code on another visit. API keys are excluded from saved profiles. Without a saved profile, learning lasts only for the current Streamlit session. This is recovery-code access, not a full account/login system. Deployment requires persistent storage to keep profiles through server replacement; do not share the runtime database in app downloads.

The knowledge base contains 54 reviewed notes from 13 sources. See `knowledge_base/README.md` for collection and refresh details. It is a starting collection, not exhaustive documentation.

## Files and validation

- `app.py`: all lesson pages, 3D integration and shared tutor interface.
- `groq_tutor.py`: Groq generation, cross-topic retrieval and Compound web lookup.
- `learner_store.py`: opt-in learner persistence.
- `tutor.py`: explicit preference updates and offline fallback.
- `lessons.py`, `knowledge_base/`, `viewer/`, `assets/`: learning content and local 3D assets.

Run `python -m unittest test_tutor -v` for retrieval, mocked web routing, personalization, profile separation and all 14 page checks. No Groq key is bundled; live Groq generation and web lookup require a working credential and have not yet been verified against the service.

The 3D assets work locally. Internet is required for Groq and web search. The app is running locally; public deployment has not been configured.

## Streamlit Cloud preparation

See DEPLOYMENT.md for upload and Secrets settings. Run `python package_deploy.py` for the credential-free upload package. The extracted package passed nine automated tests with Python 3.12 and Streamlit 1.59.2 in a fresh Windows environment; its 3D scene rendered in the browser. Linux CI and the actual Streamlit Cloud deployment have not run yet. Learning backup export/import is now available in the sidebar.
