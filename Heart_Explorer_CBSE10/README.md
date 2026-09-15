# HeartLab • CBSE Class 10

Ten study sections with illustrated PNG lesson images, text, examples and quizzes, followed by an interactive heart and a full-page Groq tutor. Based on the heart/circulation section of NCERT Life Processes: https://www.ncert.nic.in/textbook/pdf/jesc105.pdf

## Run

Install Python 3.12, run `python -m pip install -r requirements.txt`, then `python -m streamlit run app.py`. On this PC, double-click `Start HeartLab.bat`; its default address is http://localhost:8503.

## Study and explore

Use the sidebar to choose a lesson. A floating chat button opens the spacious tutor and carries the lesson context. The same conversation and preferences follow the student across sections. The final model supports mouse rotation, scroll/pinch zoom, pan, fullscreen, cutaway/exterior, label visibility, selectable parts, beat/pause and a speed slider. Part selection offers a matching tutor question. Optional flow dots show direction through the two sides of the heart.

The default **Realistic exterior** uses the textured “Realistic Human Heart” by neshallads (CC BY 4.0), bundled locally in `viewer_realistic/heart.glb`. See `viewer_realistic/ATTRIBUTION.md` for source and license. Added surface contractions illustrate a heartbeat; this source has no internal anatomy or native animation. Double-click the heart, or select **Open heart**, to switch to the simplified teaching interior in the same viewer. Double-click again or select **Close heart** to restore the exterior. All 13 interior/exterior teaching labels link to the tutor. Opening works in fullscreen and preserves manual camera control and pause state. This is a switch between two educational assets, not a geometric cut of the detailed exterior. These are educational illustrations, not medical simulations.

**Inside the opened view**, blue and red dots/arrows indicate oxygen-poor/rich routes. Inlet-valve flow runs during filling and atrial contraction; outlet flow runs during ventricular ejection. The valves, contractions, dots and phase explanation share a single clock. Pause freezes them together, the speed slider slows the cycle, and **Blood flow** hides/shows the indicators. This is a schematic animation; lungs and systemic tissues are not shown. Supporting explanation: https://www.nhlbi.nih.gov/health/heart/blood-flow and https://www.nhlbi.nih.gov/health/heart/heart-beats .

**Teaching cutaway** retains the simplified Blender model with all 13 selectable parts, chamber walls, valves, chordae and optional flow dots. Rotation stays manual in both views. Both work without an external model-hosting service; only the AI tutor needs a connection.

Editable detailed exterior: `blender/Realistic_Heart.blend` (textured mesh and a short illustrative contraction animation). Original teaching model: `blender/CBSE_Heart.blend`, rebuilt with `blender --background --python blender/build_heart.py`. This rebuild updates only the teaching model. The lesson PNG illustrations remain unchanged.

## Tutor and privacy

Set `GROQ_API_KEY` in `.streamlit/secrets.toml` or the environment. A private copy of the existing server app's configuration was used locally; no key is in source code or the ZIP. By default the tutor uses `openai/gpt-oss-120b`; `GROQ_MODEL` can override it. This app uses the lesson notes and model knowledge, not live web search. Questions, recent messages and explicit preferences are sent to Groq. All users of a shared key share provider quotas. Rate limits and outages show errors rather than fabricated answers. The tutor provides educational explanations, not medical diagnosis.

No external student database is configured. Session progress, chat and preferences can be downloaded and restored as JSON. Backups exclude API credentials. Anyone holding a backup can read its chat contents.

## Deploy

This app lives in the `Corporate_training` monorepo and deploys straight from it; the ZIP is only for offline hand-off.

In Streamlit Community Cloud, create an app pointing at repository `sanjula2003git/Corporate_training`, branch `main`, main file path `Heart_Explorer_CBSE10/app.py`, Python 3.12. Then open **Advanced settings -> Secrets** and add:

    GROQ_API_KEY = "your-key"

`.streamlit/secrets.toml` is deliberately gitignored, so the deployed app reads its key only from that Secrets panel. Everything else the app needs is committed: `assets/`, both complete viewer directories (`viewer/` and `viewer_realistic/`), and `.streamlit/config.toml`. The runtime needs neither Blender nor Node.js; the GLB and JavaScript are bundled and served as Streamlit component static files. The `blender/` sources are committed for editing only and are unused at runtime.

`HeartLab_Deployment.zip` (`python package_app.py`) is excluded from git because it exceeds GitHub's 100 MB per-file limit, and it duplicates files already in the repo.

## Checks

Run `python -m unittest test_app -v`. Tests check all study pages and tutor navigation, mocked AI behavior and explicit failures, diagram availability, GLB validity, all clickable part IDs, four removable covers, Blender source and animation presence.

Verified locally: five automated tests passed; browser checks covered pause, fullscreen, cutaway/exterior, manual rotation and selected-part handoff. The live Groq tutor answered a left-ventricle wall-thickness question in the app. This is a local app; it has not been published to Streamlit Cloud.

## Textured teaching interior

The opened model now uses embedded tissue colour, normal and roughness textures, denser chamber-wall relief and warm vessel/valve materials. Its anatomy is still simplified and is separate from the artist exterior. Editable source: `blender/Lifelike_Interior.blend`. Rebuild with `blender --background --python blender/build_lifelike_interior.py`. The script generates the interior in `viewer_realistic/teaching-heart.glb`.

## Artist interior replacement (current default)

Double-click in Realistic exterior now opens the downloaded Beating Heart by Dreamwasabducted / jalmer, with its original skinned geometry and skeletal animation. This supersedes the generated interior described above. Legacy Teaching cutaway is still separate. Credits: viewer_realistic/ATTRIBUTION.md. Material compatibility and blue diffuse-region colouring were adjusted. Labels are approximate. Flow dots and phase descriptions remain a schematic overlay, not calibrated to the artist motion.
