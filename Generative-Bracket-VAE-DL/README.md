# Generative AI for Lightweight Mechanical Bracket Design Using a VAE

A Mechanical Design + Deep Learning teaching project. A variational autoencoder learns 64×64 bracket silhouettes, samples a continuous latent design space, and generates new candidates. Candidates are screened for fixed mounting regions and connected material before ranking by material area.

## Engineering boundary

Pixel area is only a mass proxy for equal material and thickness. Connectivity is not proof of stiffness, strength, fatigue life, buckling resistance, manufacturability, or safety. Generated candidates require proper CAD reconstruction, loads, constraints, FEA, verification, and qualified engineering review.

## Files

- `Generative_Bracket_Design_VAE.ipynb`: runnable Colab notebook.
- `app.py`: interactive Streamlit latent-design companion.
- `bridge.py`: shared nine-stage teaching registry.
- `story.py`: bracket, validity, and latent-space illustrations.
- `tools/build_notebook.py`: reproducible notebook generator.

Every notebook stage has a Smart-Construction-style illustration holder and navigation links. After deployment, replace `https://generative-bracket-vae.streamlit.app` in the generator and rebuild.

The Streamlit companion contains a catalog of 32 dedicated technical illustration scenes distributed across all teaching stages.
