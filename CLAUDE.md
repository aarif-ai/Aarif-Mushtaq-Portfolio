# CLAUDE.md — Aarif-Mushtaq-Portfolio

Personal portfolio of Aarif Mushtaq (B.Tech AI & Data Science, University of Kashmir).
A polished, animated, fast static site generated with Python. Hosted on Netlify.
This is a long-lived site: Aarif updates it every few months (next: March 2027) by editing YAML only.

## 1. Content rules (highest priority — never break these)
- `content/*.yaml` is the ONLY source of text. Templates render it verbatim. Never rephrase, add adjectives, add claims or "improve" copy in templates.
- If a page needs text that isn't in the YAML, STOP and ask Aarif. Never invent metrics, users, results, dates, testimonials, logos or skills.
- Empty lists (`screenshots: []`, `photos: []`) and `TODO` comments mean "not available yet" → render nothing, never a placeholder.
- Forbidden on the site, always:
  - The CampusHub AI Event Assistant (not working yet) — no mention at all.
  - Any results, accuracy numbers, charts or conclusions for the Agent Diversity research (none exist). Decorative animations must never look like data.
  - Lines-of-code counts. Skill bars, percentages, star ratings or level meters.
  - Chatbots, AI widgets, analytics, trackers, cookie banners. Phone number.
  - The phrases "vector database" or "semantic search" for CampusHub.
  - Buzzwords: passionate, innovative, cutting-edge, leverage, synergy, seamless, robust, world-class, ninja, guru, rockstar.
- Private repos: show "Code available on request (private repository)" as plain text, never a link.
- `build.py` enforces the checkable parts of these rules (see §4) and must fail the build on a violation.

## 2. Stack
- **Python 3.11 + Jinja2 + PyYAML** → static HTML. `build.py` renders `templates/` with `content/*.yaml` into `dist/` and copies `static/` into `dist/` (except `originals/` folders and `diagrams/`, which are inlined into pages).
- Front end: hand-written HTML, CSS and vanilla JavaScript. No React, Vue, Tailwind, jQuery, GSAP or any CDN. No npm.
- Fonts: self-hosted WOFF2 in `static/fonts/` — Inter (variable) for text, JetBrains Mono for labels/code. Latin subset only, `font-display: swap`, keep the font licence files. Preload only the body font.
- `dist/` is generated: never edit it by hand, never commit it.

```
content/      site.yaml research.yaml projects.yaml skills.yaml now.yaml leadership.yaml resume.yaml
templates/    base.html  index.html  case_study.html  resume.html  404.html
              view-transitions.css  (rendered into dist/css/)
              og.html               (dev-only: drawn into static/img/og.png, never published)
              partials/*.html       (incl. macros.html)
static/       css/  js/  fonts/  diagrams/ (inlined, not copied)
              img/   (originals/ git-ignored)     docs/  (originals/ git-ignored)
              favicon.ico  favicon-16.png  favicon-32.png  apple-touch-icon.png
scripts/      make_public_resume.py  make_icons.py  make_og.py   (maintenance; need requirements-dev.txt)
build.py  requirements.txt  requirements-dev.txt  netlify.toml  .gitattributes
README.md  CLAUDE.md  BUILD_STEPS.md
dist/         ← generated output (git-ignored); Netlify publishes this
```
Local run: `python build.py` then `python -m http.server 8000 --directory dist`.

## 3. Design system — "research lab, dark first"
- Feel: precise, calm, technical, premium. Dark theme by default with a light theme toggle; follows `prefers-color-scheme` until the visitor chooses.
- Colour via CSS custom properties only. Starting point (adjust only to pass contrast): background `#0a0e14`, surface `#111823`, border `#1e2a3a`, text `#e6edf3`, muted `#9aa7b6`, accent `#5eead4` (teal), accent-2 `#818cf8` (indigo). Light theme equivalents with the same contrast. Every text/background pair ≥ 4.5:1 (≥ 3:1 for large text and UI borders).
- Type scale with `clamp()`; body 1rem–1.125rem, line-height ~1.6, max line length ~70ch. Mono font for eyebrows, tags, dates, status pills.
- Layout: mobile-first; content max-width ~1100px; generous spacing on an 8px scale. Home page: sticky header with section links and active-section highlight.
- Components: status pill (ongoing = accent, complete = accent-2), tech tags, cards with subtle border + hover glow, stat counters, timeline, decision cards, sticky table of contents on case studies.

## 4. Motion (beautiful, but never at the cost of speed or accessibility)
Allowed effects — and only these unless Aarif approves more:
1. **Hero network canvas**: slow drifting nodes joined by faint lines (a nod to LLM agent teams). `<canvas aria-hidden="true">`, ≤ 60 nodes, device-pixel-ratio capped at 2, paused when off-screen (IntersectionObserver) or tab hidden. Reduced motion → draw one static frame.
2. **Scroll reveal**: sections fade/rise in using CSS scroll-driven animations (`animation-timeline: view()`) inside `@supports (animation-timeline: view())`. Without support, content is simply visible.
3. **Reading progress bar**: `animation-timeline: scroll(root)`, CSS only.
4. **Stat count-up**: the HTML always contains the final number; JS animates from 0 once when visible. Reduced motion or no JS → final number shown.
5. **Card glow**: radial highlight that follows the pointer via CSS variables set on `pointermove`. No effect on touch devices.
6. **Page transitions** between home and case studies: cross-document View Transitions (`@view-transition { navigation: auto; }`) with shared names on project titles.
7. **Diagram draw-in**: SVG strokes animate with `stroke-dashoffset` on a view timeline.
8. **Theme toggle**: smooth colour transition; choice saved in `localStorage` (wrapped in try/catch).
9. **Hover lift** (mouse only, approved later): cards rise 3px (via `translate`, so it never fights the scroll reveal's `transform`), buttons 1px; 150–200ms.
10. **`<details>` fade** (approved later): "Show full details" content fades and drops in on open (300ms) and the chevron turns; closing is instant.
11. **Mobile menu** (approved later): the Menu button opens and closes the link panel (also closes on Escape and on choosing a link). It appears instantly; any future open/close animation must follow the rules below.
Rules for every effect:
- Animate only `transform` and `opacity` (plus `stroke-dashoffset` for diagrams). 150–600ms, ease-out. Nothing loops except the hero canvas.
- Everything (items 1–11) is wrapped in `@media (prefers-reduced-motion: no-preference)` or checked with `matchMedia` in JS. The site must look complete and polished with all motion off.
- No scroll-jacking, no custom cursor, no autoplay video, no parallax on text.

## 5. Accessibility (WCAG 2.1 AA)
Semantic landmarks, `lang="en"`, one `<h1>` per page, ordered headings, skip link, visible focus styles (`:focus-visible`), full keyboard use, theme toggle is a `<button>` with `aria-pressed`, meaningful `alt` text from YAML, link text says where it goes, no information by colour alone.

## 6. Performance budget (mobile)
- Lighthouse ≥ 95 in Performance, Accessibility, Best Practices, SEO.
- JS ≤ 30 KB total (uncompressed), CSS ≤ 40 KB, fonts ≤ 150 KB total, each image ≤ 150 KB `.webp` with `width`/`height`, `loading="lazy"` below the fold. PNG is allowed only for `og.png` (link previews) and the favicons/apple-touch icon (`.ico`/`.png`), where `.webp` isn't widely supported.
- No layout shift (CLS < 0.05). Scripts loaded with `defer`. The only blocking script allowed is a tiny theme script in `<head>` to avoid a colour flash.
- Content Security Policy in `netlify.toml` allows only `'self'` — so no inline `<script>` or inline `style=""` attributes; put everything in files.

## 7. build.py requirements
- Load every `content/*.yaml`; render with `jinja2.StrictUndefined` (a missing key must crash the build); autoescape on; a small markdown-ish filter for `*italic*` only.
- Output: `dist/index.html`, `dist/<slug>.html` per project (from `case_study.html`), `dist/404.html`; copy `static/` into `dist/`.
- Fail the build (non-zero exit, clear message) if the rendered HTML contains: the forbidden phrases in §1, the word "TODO", a phone number pattern, or a local link/image/`src` that doesn't exist in `dist/`.
- Print a short summary: pages built, total size of HTML/CSS/JS/fonts vs the §6 budget.
- Plain, readable Python with type hints and docstrings — Aarif must be able to explain every function.

## 8. How to work with Aarif
- Follow `BUILD_STEPS.md`. Do only the current step; then stop and list what changed and what Aarif should check.
- Explain each change in 2–3 plain lines, and name any concept he may not know (e.g. view timeline, CSS custom properties, StrictUndefined) with a one-line explanation.
- Never commit or push. Suggest a Conventional Commits message (`feat:`, `fix:`, `style:`, `docs:`, `build:`).
- Before finishing a step: run `python build.py`, make sure it passes, and re-check the changed pages against §1.
