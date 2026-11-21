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
Rules for contributors (including Claude Code): see `CLAUDE.md`. Build plan: `BUILD_STEPS.md`.
