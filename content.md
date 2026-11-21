# Portfolio content — Aarif Mushtaq (approved copy)

Source of truth for every word on the site. Claude Code must copy text from here verbatim.
Every claim is checked against Master_Profile.md and Resume v1 (21 Nov 2026).
Lines starting with `TODO:` are things Aarif still has to supply. Never fill them with invented content.

Last updated: 21 Nov 2026

---

## 1. Hero (index.html)

**Aarif Mushtaq**
B.Tech in Artificial Intelligence & Data Science, University of Kashmir · 2025–2029

I do faculty-supervised research on open-weight LLM agent teams and build tested, database-backed web applications in Python.

Looking for AI/ML and software engineering internships.

Buttons: Resume (PDF) → `assets/docs/Aarif_Mushtaq_Resume_v1.pdf` · GitHub → https://github.com/aarif-ai · LinkedIn → https://www.linkedin.com/in/aarif-mushtaq-167708398 · Email → mailto:aarifmushtaq542@gmail.com

---

## 2. Research (index.html)

### 2.1 Same Model or Mixed Models? Error Correlation in Open-Weight LLM Agent Teams
Faculty-supervised B.Tech research · 2026 – present · **Status: pipeline built, no results yet**

**Question.** When three LLM agents vote on an answer, majority voting only helps if they get *different* questions wrong. I'm testing whether teams of different open-weight models make fewer shared mistakes than teams of three copies of one model.

**Setup.**
- 6 open-weight 7–9B instruction models: Qwen2.5-7B, Qwen3-8B, Llama-3.1-8B, Gemma-2-9B, Mistral-7B-v0.3, OLMo-2-7B, with pinned revisions.
- 56 three-agent teams: every combination with repeats (6 same-model, 30 two-of-one, 20 all-different).
- 4 reasoning benchmarks: GSM8K, ARC-Challenge, MMLU-Pro, StrategyQA, with 500 frozen question IDs each, a calibration/evaluation split and SHA-256 data manifests.

**What I've built.** Batched offline inference with vLLM on one NVIDIA A30 (24 GB); versioned prompts; an answer parser and scorer tested with pytest; tooling to hand-check the parser; smoke tests of all 6 models and 4 quantized checkpoints; decision, run and literature logs.

**Next step.** Validating the answer parser by hand before the full benchmark runs. This page will be updated when there are results.

Diagram: `assets/diagrams/agent-diversity-pipeline.svg` — Frozen question IDs → Versioned prompts → vLLM batched inference (6 models) → Answer parser → Scorer → (Team analysis: not run yet, drawn dashed).

Code available on request (private repository).

### 2.2 A Concentrated Review on Retrieval-Augmented Generation: Towards Reliable Question Answering over Real-World Educational Documents
Course research paper · Professional Practice & Digital Skills Lab · 2026 · Defended in a viva · [Read the paper (PDF)] → `assets/docs/rag-concentrated-review.pdf`

**Question.** How ready is RAG for answering questions over real educational documents? Syllabi, handouts and regulations are PDFs with tables and layout, and they change every year. Most RAG research was tested on clean Wikipedia text.

**Method.** A narrative review of three core papers read in full: the original RAG paper (Lewis et al., 2020), a survey of retrieval-augmented LLMs (Fan et al., KDD 2024) and a systematic review of 128 RAG studies (Brown et al., 2025). I compared them on nine aspects that matter for educational documents.

**Findings.**
- Document structure and tables get only brief treatment.
- Education is 3.12% of the 128 studies (four studies).
- Those studies use separate datasets, simple chunking and different success measures, so they can't be compared.
- The core papers report no shared benchmark for educational documents.

**Contribution.** Six challenges mapped onto the stages of a RAG pipeline (parsing, chunking, retrieval, generation, refusing when the answer isn't there, cost and privacy) and a proposed six-step study to address them.

Figure: `assets/img/rag-challenges.webp` — Fig. 6 of the paper (six challenges placed on the pipeline). Alt text: "RAG pipeline from source documents to answer, with six challenges marked at the parsing, chunking, retrieval, generation and answer stages."

**Next.** A planned study on public University of Kashmir syllabi and statutes: 3 chunking strategies (fixed-length, structure-based, table-aware) × 3 retrievers (dense, BM25, hybrid) = 9 configurations. Nothing built yet; no results.

**Limits.** Narrative review, not systematic; only three papers were read in full.

---

## 3. Projects

### 3.1 CampusHub — full case study (campushub.html; card on index.html)

Card text (index.html): **CampusHub** — a Flask platform that runs the full lifecycle of a campus event for 4 roles, with QR attendance, PDF certificates, 351 tests and CI. → Read the case study

**CampusHub: campus event management platform**
Python · Flask · SQLAlchemy · PostgreSQL · pytest · GitHub Actions

**Problem.** Running a campus event involves several people. An organiser proposes it, the department approves it, logistics prepares it, and students attend and need certificates. CampusHub puts the whole lifecycle (Draft → Submitted → Approved/Rejected → Published → Completed) in one web app, with a separate role for each person.

**My role.** Solo project. I designed and built it with AI assistance (Claude), and I can walk through and explain every module.

**Architecture.** Diagram: `assets/diagrams/campushub-architecture.svg`
Browser → Flask routes (kept thin) → 25 service modules → SQLAlchemy models → SQLite (development) / PostgreSQL. Alongside: Alembic migrations, ReportLab (PDF certificates), Resend (email), GitHub Actions CI.
Second diagram: `assets/diagrams/campushub-lifecycle.svg` — Draft → Submitted → Approved / Rejected → Published → Completed.

**Key decisions.**
1. **Business logic in a service layer, not in routes.** Routes only handle HTTP. The 25 service modules hold the rules (who can approve what, when an event can be published), so they live in one place and can be tested without a browser.
2. **Duplicate check-ins are blocked by the database, not only by code.** If two QR scans arrive at the same moment, a check in Python can pass for both. A UNIQUE constraint makes the database reject the second insert.
3. **Signed QR tokens.** Attendance QR codes carry a token signed with the server's secret key, so an edited or forged code fails verification. The same idea powers a public page that verifies certificates.
4. **Partial unique indexes** enforce exactly one Organizer and one Logistics account at the database level.

**Security.** Hashed passwords, CSRF protection, role checks on every route, login throttling, safe file uploads, security headers, expiring password-reset links.

**Testing and CI.** 351 pytest tests. GitHub Actions runs Ruff (lint) and pytest, in parallel, on every push and pull request. Schema changes go through 11 Alembic migrations. Tested on PostgreSQL 16.

**Screenshots.** TODO: 4–5 screenshots, taken after confirming the app shows "CampusHub": event dashboard, department approval screen, QR check-in, a generated certificate, public verification page. Use demo data only — no real student names, emails or phone numbers.

**What I'd do differently.**
- Deploy early and keep it live. My first deployment went down when the free hosting tier ended.
- Write the core modules myself before using AI, so understanding comes before speed.

**Links.** Code available on request (private repository) · Live demo: coming after redeployment.

### 3.2 Hostel Management System — short case study (hostel.html; card on index.html)

Card text (index.html): **Hostel Management System** — a Flask and SQLite admin app for rooms, attendance, fees, complaints, visitors and food-wastage fines. → Read the case study · GitHub

**Hostel Management System**
Python · Flask · SQLite · Bootstrap · JavaScript · [GitHub] → https://github.com/aarif-ai/Hostel-Management-System

**Problem.** Hostel administration was tracked by hand: who lives in which room, daily attendance, fees, complaints and visitors. This app puts it in one admin web app.

**My role.** Semester 2 group project. I wrote all the code; teammates helped prepare the project report.

**Architecture.** Diagram: `assets/diagrams/hostel-architecture.svg`
Admin browser → Flask app (7 modules: students, rooms, attendance, fees, complaints, visitors, food wastage) → SQLite.

**Key decisions.**
1. **One attendance record per student per day.** A UNIQUE(student, date) constraint plus an upsert means re-marking a day updates the record instead of creating a duplicate.
2. **Attendance percentage is calculated, not typed in.** Percentage = days marked Present ÷ days marked × 100. Students below 75% are listed as defaulters.
3. **Food-wastage fines are calculated per month.** Each recorded wastage incident carries a ₹20 fine. The admin applies a student's monthly total as a pending "Food Wastage Fine" fee.
4. **Admin login** uses hashed passwords (werkzeug) and Flask's session-based authentication.

**Screenshots.** TODO: 2–3 screenshots — dashboard, attendance view, wastage/fines view (demo data only).

**Known gaps (fixing now).** The secret key is hard-coded, there are no automated tests, and it isn't deployed.

---

## 4. Skills (index.html) — word-for-word from Resume v1

**Proficient** — I can write it without AI help and explain it in an interview:
Python, C, SQL · SQLite, MySQL · NumPy, Pandas, Matplotlib · Git, GitHub · Object-Oriented Programming

**Familiar** — used in projects, still need references:
C++, JavaScript, HTML/CSS, Bootstrap · Flask, Jinja2, SQLAlchemy, Alembic, PostgreSQL · pytest, GitHub Actions (CI) · Jupyter, Exploratory Data Analysis · vLLM, LLM inference and evaluation, prompt design, RAG

---

## 5. Now / Learning log (index.html)

Last updated: 21 Nov 2026

**Now**
- Semester 3 exams (Nov–Dec 2026).
- Agent Diversity research: validating the answer parser by hand before full benchmark runs.

**Next (8 Jan – 8 Mar 2027)**
- DSA in C++, every day.
- A RAG and AI-agents course, and one serious RAG/agent project.
- Rebuilding the core modules of my own projects without AI.
- Redeploying CampusHub with a live demo.

**Log** (newest first)
| Date | Entry |
|---|---|
| 21 Nov 2026 | Finalised resume v1; started this portfolio |

---

## 6. Leadership (index.html)

**Founder & Student Coordinator, VERITAS Language Club**
University of Kashmir, North Campus · Founded Sep 2026 · Paused for exams, resuming March 2027

I started a language club with support from the Campus Director and a faculty advisor, and organised 2 events with 100+ participants each:
- **VERITAS: The First Voice** (11 Sep 2026) — the inaugural debate, judged by department coordinators, with awards for Winning Team, Best Speaker and Best Rebuttal.
- **VERITAS: Beyond the Screen** — a film screening followed by a "Take Your Stand" discussion.

I planned each event: schedules, debate rules, judging score sheets, official letterhead and letters, and certificates.

Photos: TODO: 4–5 event photos from Aarif's laptop, each with a one-line caption from Aarif. Only photos the people in them are fine with.

---

## 7. About + Contact (index.html)

**About**
I'm Aarif, a B.Tech student in AI & Data Science at the University of Kashmir's North Campus (Semester 1 SGPA: 8.65/10).

When I take something on, I give it whatever it needs and see it through. That's how a college project became a 351-test application, and how a research question became a 56-team, 4-benchmark study.

I'm working towards becoming an AI engineer with strong computer science fundamentals — which is why my next three months are DSA, RAG and agents, and rebuilding my own code without AI.

Outside engineering, I write. I've completed a semi-autobiographical novella, *The Weight of Water*.

**Contact**
Open to AI/ML and software engineering internships.
Email: aarifmushtaq542@gmail.com · GitHub · LinkedIn · Resume (PDF)
Kashmir, India

**Footer (every page):** Built by hand with HTML, CSS and JavaScript, with help from Claude Code. Last updated 21 Nov 2026.
