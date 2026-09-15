# Deploy AtomLab to Streamlit

1. Upload the contents of this folder to your GitHub repository. Preserve the assets, viewer and .streamlit folders.
2. In Streamlit Community Cloud, select your repository and set the main file to app.py. Choose Python 3.12.
3. Add the following in the app Secrets settings, replacing the placeholder privately:

```toml
GROQ_API_KEY = "your-groq-key"
```

Keep quotation marks around the value. Your private API key is intentionally not included in this folder. Lessons and the 3D explorer work without it; the AI tutor requires it.

If you upload this entire folder as a subfolder in GitHub instead of its contents at the root, set the main file path to AtomLab_Deploy/app.py.

This package contains labelled illustrations and all 13 guided concepts in the 3D explorer. No Blender installation is needed.
