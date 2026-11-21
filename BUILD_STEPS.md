# Build steps — paste one prompt at a time into Claude Code

How to start each session (Command Prompt):
```
cd C:\Users\aarif\Aarif-Mushtaq-Portfolio
.venv\Scripts\activate
claude
```
Keep a second Command Prompt for the preview:
```
cd C:\Users\aarif\Aarif-Mushtaq-Portfolio
.venv\Scripts\activate
python build.py && python -m http.server 8000 --directory dist
```
Open http://localhost:8000 . After a change: stop the server (Ctrl+C) and run that last line again.

After EVERY step: read Claude's explanation → check the list → commit yourself:
```
git add .
git commit -m "<message Claude suggests>"
git push
```
If something is wrong, tell Claude Code what you see before moving on. Never skip a check.

---

## Step 0 — Rules check (no code)
```
Read CLAUDE.md, BUILD_STEPS.md and every file in content/. Don't write code.
Summarise in 6 bullets the rules you must follow, and list every TODO in content/.
```
Check: it mentions verbatim YAML text, no AI assistant, no Agent Diversity results, no skill bars, reduced-motion fallback, build.py checks.

## Step 1 — build.py and a bare page
```
Do Step 1: write build.py exactly as CLAUDE.md §7 describes (requirements.txt already exists), plus templates/base.html and a minimal templates/index.html that renders only the hero text from content/site.yaml. No CSS yet.
Then run python build.py and show me the output.
```
Check:
- `python build.py` prints a summary and creates `dist/index.html`.
- Test the guard: temporarily type `TODO` into the hero text in site.yaml → the build must FAIL. Undo it.
- Ask: "Explain StrictUndefined and why the build should fail on a missing key." Make sure you understand.

## Step 2 — Design system and fonts
```
Do Step 2: download Inter (variable, WOFF2) and JetBrains Mono (WOFF2) from their official sources into static/fonts/ with their licence files, then create static/css/ with the design tokens, dark and light themes, typography, layout container, skip link, focus styles and the sticky header with section links, following CLAUDE.md §3. Add the theme toggle (§4 item 8) with a tiny head script in static/js/.
Show me the token list and explain how the theme switch avoids a colour flash.
```
Check: dark by default; toggle switches and remembers after reload; Tab shows the skip link first and clear focus rings; 360 px width in DevTools has no sideways scroll.

## Step 3 — Hero with the network animation
```
Do Step 3: build the hero (eyebrow, name, positioning, availability, buttons for Resume, GitHub, LinkedIn, Email) and the hero network canvas exactly as CLAUDE.md §4 item 1 describes. Keep the JS readable and commented.
```
Check: animation is slow and subtle, not distracting; text is readable over it. Turn on Windows "Animation effects: off" (Settings → Accessibility → Visual effects) → the canvas is a still image. DevTools → Performance: no constant high CPU when scrolled away.

## Step 4 — Stats strip and Research
```
Do Step 4: add the stats strip (count-up, §4 item 4) and the Research section from content/research.yaml as two cards with status pills, tags, and all fields. Render the RAG figure only if the image file exists; otherwise skip it.
```
Check: numbers end at 351 / 56 / 4 / 100+; with JS disabled the real numbers show. "Ongoing — pipeline built, no results yet" is clearly visible. "Read the paper (PDF)" opens the PDF. No results or charts for Agent Diversity.

## Step 5 — Project cards and Skills
```
Do Step 5: add the Projects section (cards with pointer glow, status pill, stack tags, link to each case-study page) and the Skills section with the Proficient/Familiar definitions shown, from the YAML. No bars, icons or percentages.
```
Check: 11 Proficient and 17 Familiar items, word-for-word as the resume. CampusHub card has no GitHub link. Glow follows the mouse, nothing happens on touch.

## Step 6 — Timeline, Now, Leadership, About, Contact + scroll effects
```
Do Step 6: add the Journey timeline (upcoming item styled differently), Now / Learning log (log as a real <table>), Leadership, About and Contact from the YAML, the footer with last_updated, and the scroll reveal and reading progress bar (§4 items 2–3).
```
Check: no "TODO" or empty boxes anywhere; VERITAS says "Paused for exams, resuming March 2027"; header links highlight the current section; with reduced motion everything is simply visible.

## Step 7 — Case-study pages
```
Do Step 7: create templates/case_study.html and generate campushub.html and hostel.html from content/projects.yaml: title block with status and stack, sticky table of contents, Problem, My role, Architecture, Key decisions (as decision cards), Security/Testing when present, the reflection section, links, and a back link. Add cross-document view transitions (§4 item 6).
```
Check: clicking a project card animates into its page (Chrome/Edge); no AI assistant, no vector search, no LOC; CampusHub "My role" mentions Claude; Hostel shows the formula and ₹20 rule exactly. Interview drill: explain decisions 2 and 3 out loud without reading.

## Step 8 — Diagrams
```
Do Step 8: create the SVG diagrams listed in the YAML (agent-diversity-pipeline, campushub-architecture, campushub-lifecycle, hostel-architecture) in static/diagrams/, with <title>/<desc>, theme-aware colours, readable at 360 px, and the draw-in animation (§4 item 7). One diagram at a time — show me and wait for my OK before the next.
```
Check each: boxes match what the code really does; the "Team analysis" box is dashed and says "not run yet"; readable in light and dark.

## Step 9 — SEO, 404, favicon, social preview
```
Do Step 9: per-page <title>, meta description and Open Graph/Twitter tags from the YAML, a canonical URL placeholder in one config value, favicon.svg ("AM" monogram), 404 page in the same design, and a simple 1200×630 social preview image built as SVG then exported to PNG.
```
Check: share the local page link preview in a tool like opengraph.xyz after deploy (later); 404 looks on-brand.

## Step 10 — Audit (report only)
```
Do Step 10: audit the whole site against CLAUDE.md. Report every rule violation, budget overrun, contrast failure, missing alt text, heading-order issue and broken link. Don't fix anything yet.
```
Then yourself: Lighthouse (DevTools → Lighthouse → Mobile) ≥ 95 in all four; validator.w3.org/nu on each page in dist/. Fix, rebuild, commit.

## Later — screenshots and photos
```
I've put images in static/img/originals/. Convert them to .webp (max 1600 px wide, ≤150 KB), add them to the YAML entries I tell you with these captions/alt text: <...>. Add static/img/originals/ to .gitignore.
```
CampusHub screenshots: demo data only — no real names, emails or phone numbers.
