# AtomLab

A separate Streamlit atomic-structure learning app for Class 10 learners, revisiting foundations usually introduced earlier. Thirteen illustrated lessons and quizzes lead to a fourteenth page containing an interactive 3D atom explorer. The full-page Groq tutor is accessible from every lesson and from individual particles.

## Run locally

Use Python 3.12. Install `requirements.txt`, then run `streamlit run app.py` from this folder. All diagrams and Three.js assets are local. Lessons and 3D work without an API key; AI replies require a configured Groq key and internet access.

## Deploy yourself

1. Extract `AtomLab_Ready_To_Deploy.zip` and upload its contents to your GitHub repository. Preserve `assets`, `viewer` and `.streamlit` directories.
2. In Streamlit Community Cloud, select the repository and `app.py` as the main file. Use Python 3.12.
3. In the app's Secrets settings add your own key using TOML syntax:

```toml
GROQ_API_KEY = "your-key-here"
```

The quotes around the key value are required. Never put the real key in GitHub or in the Python/JavaScript source. The deployment ZIP excludes the local private secrets file. `GROQ_MODEL` can optionally be set as an environment variable; the default is `openai/gpt-oss-120b`.

## Explorer controls

Choose an example or edit protons, neutrons and electrons. Drag to rotate manually, scroll/pinch or use +/− to zoom, and use Full screen for a larger view. Click/tap a particle for its explanation; Ask opens the full-page tutor. Double-click a nucleon or use Spread nucleus to separate the pictured particles. Optional electron motion is off initially. Shell rings can be hidden. The model never rotates automatically.

This is a teaching/counting model, not a quantum or nuclear simulation. Custom combinations can be hypothetical or unstable. The shell pattern is deliberately restricted to 2,8,8,2 for at most 20 electrons; arbitrary ions may require a more advanced electronic-structure model. Nuclear sizes and particle separations are enlarged.

## Learning and privacy

Chat history, progress and explicit learning preferences live in the current Streamlit session. Download a progress backup to restore them later. No external learner database is required. Preferences, recent chat, relevant notes and selected atom counts are sent to Groq when asking the tutor. There is no live web search. All visitors share your provider account allowance; provider limits still apply.

See SOURCES.md for curriculum context. Three.js and OrbitControls are distributed under their included MIT license in `viewer/THREE-LICENSE.txt`. Illustrations and lesson text were created for this app.

## Guided 3D lessons

The model’s Learn a concept in 3D menu covers all 13 study sections. Choose a concept and move through its labelled examples; the model and counts change together. Ask about the concept opens the full-page tutor with that lesson and the current counts. Shells have K/L/M/N labels and electron counts; labels identify the outermost occupied shell. Every lesson illustration includes direct labels and a particle legend.
