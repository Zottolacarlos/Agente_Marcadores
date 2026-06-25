# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Continuity across devices (READ FIRST)

This project is worked on from multiple Windows machines at **different absolute paths**, so Claude Code's `.jsonl` session files and `/resume` do **not** sync between them. Cross-device continuity is handled through git instead:

- **At the start of every session, read `.claude/CONTEXTO.md`** — it's the versioned handoff log: current state, what we were doing, decisions, and next steps.
- **At the end of every session, update `.claude/CONTEXTO.md`** (last session, in-progress work, new decisions) so the next device picks up the thread. Keep it short — it's a live handoff, not an append-only history.
- The user's workflow is: `git pull` → work → ask Claude to update `CONTEXTO.md` and commit → `git push`. One device at a time.
- Do **not** rely on the harness memory dir (`~/.claude/projects/.../memory/`) for cross-device state — it's local to one machine. Durable, portable context goes in `.claude/CONTEXTO.md`.

## What this is

Local MVP that curates browser bookmarks and turns them into an actionable plan. Given an exported `bookmarks.html` or a live Chrome/Edge profile, it filters to a target folder (default `Pendientes`), validates links, detects duplicates, classifies each link by rule-based keywords, scores priority, and emits Markdown/CSV reports plus a 7-day reading schedule. Privacy-first: runs locally, never commit real bookmarks. (Code and reports are in Spanish.)

## Commands

```bash
# Setup (README uses pip + requirements.txt; pyproject also has a Poetry dependency group)
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run web UI (FastAPI + Jinja2) at http://localhost:8000
uvicorn app.main:app --reload

# CLI
python -m app.cli analyze --file data/input/bookmarks.html --folder Pendientes
python -m app.cli analyze-browser --browser chrome --folder Pendientes   # or --browser edge
# Useful flags for large folders: --limit/-l N  and  --skip-validation (no network calls)

# Tests (pytest; pyproject sets pythonpath=["."] so `app` imports resolve)
pytest
pytest tests/test_priority_scorer.py::test_priority_score_high   # single test

# Lint (dev dependency)
ruff check .
```

## Architecture

The core is a single synchronous pipeline. Both entry points (`app/cli.py`, `app/routers/*`) collect a `list[Bookmark]` from a source, then hand off to **`app/services/analyzer.py::run_analysis`**, which is the orchestrator. To change analysis behavior, this is almost always the file to start in.

**Pipeline order inside `run_analysis`:** folder filter → optional `limit` slice → `normalize_url` → `detect_duplicates` → per-bookmark (`validate_url` → `classify` → `score_bookmark`) → sort by score desc → `build_7_day_schedule` → `write_reports` → persist via `SQLiteRepository`. Returns an `AnalysisSummary`. Each stage is an isolated function in `app/services/`, so they can be unit-tested in isolation (see `tests/`).

**Layers:**
- `app/main.py` — FastAPI app; calls `init_db()` on startup; mounts `web_router` (HTML pages) and `api_router` (JSON under `/api`).
- `app/routers/` — `web_router.py` serves Jinja templates from `app/templates/`; `api_router.py` exposes `/api/analyze`, `/api/reports`, `/api/bookmarks`. Both routers parse sources then delegate to `run_analysis`.
- `app/services/` — the pipeline stages (parsing, normalization, validation, classification, scoring, scheduling, reporting). Sources: `html_bookmark_parser.py` (BeautifulSoup over exported HTML) and `chromium_bookmark_reader.py` (reads Chrome/Edge `Bookmarks` JSON from Windows `AppData` profiles `Default`/`Profile N`).
- `app/models/` — Pydantic models. `Bookmark` is raw input; `BookmarkAnalysis` is the scored result; `AnalysisSummary` is the response.
- `app/repositories/sqlite_repository.py` + `app/database.py` — single SQLite table `bookmarks_analysis`. **`save_analysis` truncates the table (`DELETE FROM`) on every run** — it stores only the latest analysis, not history.
- `app/config.py` — `settings` singleton; resolves `data/` paths and creates `reports_dir`/`input_dir` at import time. Reads `REQUEST_TIMEOUT` and `OPENAI_API_KEY` from `.env`.

## Key conventions and gotchas

- **Classification is keyword rules**, not AI. `rule_classifier.py::RULES` is an ordered dict; first category whose keyword appears in `"{title} {url} {folder}".lower()` wins, else `"desconocido"`. Order matters — earlier categories take precedence. `ai_classifier.py` is a deliberate no-op stub (returns `None`) reserved for a future OpenAI integration; `OPENAI_API_KEY` is wired through config but unused.
- **Scoring → action mapping lives in `priority_scorer.py`.** It returns `(score 0–100, action, reason)`. Status strings (`OK`, `BROKEN`, `REDIRECTED`, `FORBIDDEN`, `TIMEOUT`, `UNKNOWN`, `NOT_VALIDATED`) and action strings (`ver_esta_semana`, `ver_luego`, `archivar`, `revisar_o_borrar`, `borrar_probable`) are bare string contracts shared across the scorer, scheduler, and report generator — change them in all three together.
- **`skip_validation` sets status to `NOT_VALIDATED`** and skips all network calls; it is intentionally *not* penalized in scoring. Use it for large folders.
- **Duplicate detection is by normalized URL only** (`normalize_url` lowercases host, strips `www.` and trailing slash, drops fragment, keeps query). No fuzzy/domain matching yet.
- **Reports** are written to `data/reports/` (`pendientes_priorizados.md`, `links_rotos.md`, `duplicados.md`, `cronograma_7_dias.md`, `resultado.csv`) and served via `GET /reports/{name}` with a path-traversal guard.
- Firefox is unsupported (TODO). `bookmark_web_ui.patch` is a stray patch file in the repo root.
