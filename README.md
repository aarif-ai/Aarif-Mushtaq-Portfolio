# Aarif Mushtaq — Portfolio

Static portfolio generated with Python (Jinja2 + YAML) and hand-written HTML, CSS and JavaScript.

- `content/` — all site text as YAML (the only place to edit content)
- `templates/` — Jinja2 page templates
- `static/` — CSS, JS, fonts, images, diagrams, PDFs
- `build.py` — renders everything into `dist/` (what Netlify publishes)

Run locally (Windows Command Prompt):
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python build.py
python -m http.server 8000 --directory dist
```
## Maintenance scripts (not needed by Netlify)
Install their tools once: `pip install -r requirements-dev.txt` (PyMuPDF and Pillow; `make_og.py` also needs Chrome, Edge or Chromium installed).

| Script | Run it when | What it does |
|---|---|---|
| `python scripts/make_public_resume.py` | the resume PDF changes | Reads the private `static/docs/originals/Aarif_Mushtaq_Resume_v1.pdf` (git-ignored) and writes `static/docs/Aarif_Mushtaq_Resume.pdf` with the phone number removed, then verifies it. `--preview compare.png` saves a before/after image. |
| `python scripts/make_icons.py` | the photo changes | From `static/img/originals/aarif-original.jpg` (git-ignored): the header avatar `img/aarif-64.webp`, `favicon.ico`, `favicon-16.png`, `favicon-32.png` and `apple-touch-icon.png`. `--preview zoom.png` shows the 32px icon enlarged. |
| `python scripts/make_og.py` | name, eyebrow, availability or photo change | Renders `templates/og.html` with headless Chrome into the link-preview image `static/img/og.png` (1200×630). Set `CHROME` to the browser path if it isn't found. |

Then run `python build.py` as usual.

Rules for contributors (including Claude Code): see `CLAUDE.md`. Build plan: `BUILD_STEPS.md`.
