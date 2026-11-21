# CLAUDE.md — Aarif-Mushtaq-Portfolio

Personal portfolio of Aarif Mushtaq (B.Tech AI & Data Science, University of Kashmir).
Static site: plain HTML, CSS and a little JavaScript. Hosted on Netlify from this repo.

## 1. Content rules (most important)
- `content.md` is the ONLY source of text. Copy it verbatim. Do not rephrase, add adjectives, add claims, or "improve" copy.
- If a page needs text that is not in `content.md`, STOP and ask Aarif. Never invent metrics, users, results, dates, testimonials or skills.
- A `TODO:` line in `content.md` stays a visible placeholder or is left out — never filled with made-up content.
- Forbidden on this site, always:
  - The CampusHub AI Event Assistant (not working yet) — no mention at all.
  - Any results, accuracy numbers or conclusions for the Agent Diversity research (none exist).
  - Lines-of-code counts.
  - Skill bars, percentages, star ratings or "level" meters.
  - Chatbots, AI widgets, analytics, trackers, cookie banners.
  - Buzzwords: passionate, innovative, cutting-edge, leverage, synergy, seamless, robust, world-class, ninja, guru, expert.
  - The phrases "vector database" or "semantic search" for CampusHub.
  - Phone number.
- Private repos are shown as "Code available on request (private repository)" — never link them.

## 2. Tech constraints
- No frameworks, no build step, no npm dependencies in the site, no CDNs, no web fonts. System font stack only.
- One shared stylesheet `site/css/style.css`; one small script `site/js/main.js` (mobile nav only). Pages must work fully with JavaScript turned off.
- Everything public lives in `site/`. `netlify.toml` publishes `site/` only, so `content.md`, `CLAUDE.md` and `README.md` are not served.
- Diagrams are hand-written inline-friendly SVG files in `site/assets/diagrams/`, each with `<title>` and `<desc>`, using `currentColor` so they work in dark mode.

## 3. Structure
```
site/
  index.html            Hero → Research → Projects (cards) → Skills → Now → Leadership → About + Contact
  campushub.html        CampusHub full case study
  hostel.html           Hostel Management System case study
  404.html
  css/style.css
  js/main.js
  assets/img/           screenshots and photos (.webp)
  assets/diagrams/      .svg diagrams
  assets/docs/          Aarif_Mushtaq_Resume_v1.pdf, rag-concentrated-review.pdf
  favicon.svg
content.md  CLAUDE.md  README.md  netlify.toml
```
Case-study pages use the same order: Problem → My role → Architecture → Key decisions → Security/Testing → Screenshots → What I'd do differently / Known gaps → Links.

## 4. Accessibility (WCAG 2.1 AA)
- Semantic HTML: one `<h1>` per page, headings in order, `<header> <nav> <main> <section> <footer>`, `lang="en"`.
- "Skip to content" link; visible focus styles; every interactive element reachable by keyboard.
- Text contrast ≥ 4.5:1 in both light and dark (`prefers-color-scheme`).
- Every image has meaningful `alt` text (decorative images: `alt=""`). Respect `prefers-reduced-motion`.
- Links say where they go ("Read the CampusHub case study", not "click here"). External links open in the same tab.

## 5. Performance
- Mobile-first CSS (base styles for ~360px, `min-width` media queries upward).
- Each HTML page < 50 KB; CSS < 20 KB; JS < 5 KB.
- Images: `.webp`, max 1600 px wide, ≤ 150 KB each, with `width`, `height` and `loading="lazy"` (except above-the-fold).
- Target Lighthouse ≥ 95 for Performance, Accessibility, Best Practices and SEO on mobile.

## 6. SEO / meta
Each page: `<title>`, meta description, Open Graph title/description, canonical URL (add once the Netlify URL is known), `favicon.svg`.

## 7. How to work with Aarif
- Work in small steps. Do only the step asked; then stop and list what changed and what Aarif should check.
- Explain every change in 2–3 plain lines (what and why). Aarif is learning HTML/CSS and must be able to maintain this site himself.
- When a choice involves a concept he may not know (e.g. CSS grid, media queries, `srcset`), name it and explain it briefly.
- Never commit or push unless Aarif says so. Suggest a commit message in Conventional Commits style (`feat:`, `fix:`, `docs:`, `style:`).
- Before finishing a step, re-read the changed pages against `content.md` and Section 1 of this file, and report any mismatch.
