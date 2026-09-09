# Streamlit Community Cloud deployment

## Upload

Run `python package_deploy.py`, then extract `Streamlit_Deployment.zip`. Upload the extracted contents to the ROOT of a GitHub repository. Include the hidden `.streamlit` and `.github` folders, plus all of `viewer`, `assets`, and `knowledge_base`. Do not upload the entire unfiltered local app directory: it contains private server secrets and may contain learner records.

The package includes the 9.7 MB GLB and local JavaScript modules. Blender, Node.js, a GPU on the server, and Windows batch files are not needed. The viewer uses relative URLs and renders on the visitor's device.

## Configure hosting

At https://share.streamlit.io create an app from that repository. Choose your actual branch, entrypoint `app.py`, and Python **3.12** in Advanced settings. Dependencies are in `requirements.txt` (Streamlit 1.59.2).

In the Streamlit dashboard's Secrets field, set:

```toml
GROQ_API_KEY = "your-new-private-key"
```

Use a replacement for the key previously shared in chat. Never put the real key in GitHub, the ZIP, or `app.py`. The local secret file is excluded from the package. Your cloud secret is separate from the local copy; configure it in Streamlit even though the app connects automatically on your PC.

Official setup: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
Secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

## Learning progress

SQLite persistence is local to the server. Cloud storage must be treated as temporary; a recovery code alone cannot restore a database that has disappeared. The sidebar now offers **Download my learning backup** and **Restore a learning backup**. Backups include preferences, chats and progress, but no API key or recovery token. Automatic durable cross-device storage still requires an external database; it is not configured in this app.

## Capacity and web search

All visitors share the configured Groq account's allowance. The app limits simultaneous Groq requests to two per process and handles quota, busy and network errors. This is not a guarantee of capacity for a class of concurrent students. Check account quotas and hosting usage before a larger rollout.

The last live Compound web lookup returned HTTP 413 even for a short question. The app continues with its initial AI response and explicitly reports that web verification failed. Treat live web search as an unresolved provider/account issue, not a verified deployment feature. Deployment alone may not resolve it.

## Validation

`python -m unittest test_tutor -v` uses simulated Groq responses and never needs a real key. It checks all lesson/model chat entry points, the dedicated tutor page, cross-topic requests, web routing/fallback, preferences, profile isolation and backup validation. GitHub Actions runs these checks on Linux/Python 3.12 when the repository is uploaded; that workflow has not run yet locally.

After deployment: open every page, load and rotate the 3D model, test fullscreen and topic selection, ask the blade/tower connection question, and download/restore a learning backup. Verify a second browser session has separate chat state. A public deployment and live browser validation on Streamlit Cloud are still required.
