# JobHunterAgent — Phase 1 (Archived)

Automated job-search assistant for Portal B, Portal A, and Portal C: a Counter → Scraper →
Validator pipeline driven by a local dashboard, plus a manual "Career" application tracker.

**Status: Phase 1, stopped here.** See [Limitation](#limitation-why-this-stopped) below.

## Per-file documentation
Every `.py` file has a matching doc in [`docs/`](./docs) (e.g. `docs/scraper.py.md`)
covering its role, functions, and dependencies.

## Architecture
- **Counter** (`job_counter.py` + `counter_portal_b.py` / `counter_portal_a.py` / `counter_portal_c.py`)
  — estimates total job count per keyword/location before scraping.
- **Scraper** (`scraper.py` + `scraper_portal_b.py` / `scraper_portal_a.py` / `scraper_portal_c.py`)
  — pulls job listings via Selenium, writes to `scraper_jobs.xlsx` → `jobs.csv`.
- **Validator** (`validator.py` + `validator_portal_b.py` / `validator_portal_a.py` / `validator_portal_c.py`)
  — opens each scraped job's URL and classifies it Internal/External/Ineligible.
- **Dashboard** (`dashboard_server.py` + `dashboard_*.py`) — local web UI (`localhost:8080`)
  to configure, launch, and monitor the above as subprocesses, plus a Career tab for
  manually tracked applications.
- Shared infrastructure: `create_driver.py` / `antibot_helpers.py` (browser lifecycle),
  `search_state.py` (resumable scrape state), `tracker.py` / `blacklist_manager.py`
  (persistence), `workflow_tracker.py` (progress/logging).

## Modules
- **Scraper modules (per portal)** — one module per job portal handles discovery of postings for that portal.
- **create_driver** — sets up the browser session used for scraping.
- **search_state** — tracks scraping progress (current page, job counts, completed flags) per portal so runs can resume instead of restarting.
- **tracker** — writes discovered jobs to a job store (Excel/CSV) and syncs to a master jobs file.
- **job_counter** — determines total postings/pages available for a search before scraping begins.
- **blacklist_manager** — maintains a blacklist of postings/companies (Job Title, Company, Portal, URL, Reason, Date Added) to exclude from future runs.
- **validator** — revisits saved postings with status `Scraped` or `Eligible` and blank Internal/External field, checks each URL, and updates status to `Ineligible` if expired, or sets Internal/External based on whether the apply button is internal or external. Rows it can't classify are left untouched and picked up again on the next run.
- **career_tracker** — loads/saves application records (`career_apps.csv`) and career-site records (`career_sites.csv`).
- **workflow_tracker** — reports live stage updates and logs for each running workflow (e.g. Create Order → Connecting to Browser → Cycle → Complete, as used by the validator).
- **dashboard_workflows** — manages workflow runs, subprocess execution, logging, and config loading for the dashboard.
- **dashboard_server** — runs the local dashboard (`python dashboard_server.py`, served at `http://localhost:8080`).
- **dashboard_jobs / dashboard_scraper / dashboard_career / dashboard_detail / dashboard_ui** — build the Jobs, Scraper, Career, and Workflow Detail pages of the dashboard, plus shared styling.
- **dashboard_backup** — reads `jobs.csv` and `blacklist.csv` and writes a single styled `.xlsx` (one tab per status) into a local OneDrive-synced folder so it's backed up to the cloud automatically.

## Data stored
**Jobs (`jobs.csv` / scraper Excel file)** columns: `Job ID, Job Title, Company, Portal, Location, URL, Status, Internal/External, Applied Date, Last Checked, Description, Notes`

**Applications (`career_apps.csv`)** columns: `company, link, credential, credtype, passhint, role, location, date, stage, substage, ghostedsub, jobid, notes`

**Career sites (`career_sites.csv`)** columns: `name, url, cred, notes`

**Blacklist (`blacklist.xlsx`)** columns: `Job Title, Company, Portal, URL, Reason, Date Added`

Job status values seen in the code: `Scraped, Eligible, Applied, Ineligible, Hold, Blacklist`.

## Dashboard
A local web server (`dashboard_server.py`) provides:
- **Jobs tab** — filter by status and portal, browse discovered postings, paginated.
- **Scraper tab** — Request / Workflow / Log sub-tabs, with a status legend for workflow stages.
- **Career tab** — Applications and Job Sites sub-tabs.
- **Workflow detail page** — shows a single workflow's status and log.

## Limitations — why this stopped
1. **Scraping policy.** Portal A, Portal B, and Portal C's terms of service prohibit
   automated scraping of their job listings. This project was built and got working
   end-to-end against all three portals, but continuing to run it against their live
   sites isn't something to keep doing. This is the main reason Phase 1 is being
   archived rather than developed further in its current scraping-based form.

   **Code removed for this reason:** `antibot_helpers.py`, `portal_c_helpers.py`,
   `scraper_portal_c.py`, `counter_portal_c.py`, `validator_portal_c.py`,
   `scraper_portal_a.py`, `counter_portal_a.py`, `validator_portal_a.py`,
   `scraper_portal_b.py`, `counter_portal_b.py`, `validator_portal_b.py`,
   `portal_b_helpers.py` — these files are kept as placeholders
   (`# code were deleted due to legal issue`), with all Anti-bot-bypass and
   Portal A/Portal B/Portal C scraping automation stripped out due to legal/ToS issues.

   `scraper.py`, `job_counter.py`, and `validator.py` (the orchestrators that call
   into the files above) were edited so they still **load and run** without
   crashing outright — their imports of the now-empty modules were moved from
   module level to inside each portal's specific code branch. This means:
   picking a portal that has no scraped data / isn't reached simply logs and
   skips as before; only a code path that actually tries to call into a removed
   module (e.g. running the Portal B branch) will fail there, with a clear
   `ImportError`, rather than the whole script refusing to start. This repo will
   not actually scrape or validate any portal — the automation itself is gone —
   but the dashboard, tracker, and orchestration code around it still run.
2. **Storage didn't scale.** CSV/XLSX read-and-rewrite-whole-file on every save doesn't
   hold up — `jobs.csv` hit 13MB (~8,500 rows), and `tracker.py` was rewriting it on
   every scraped page (30+ pages per keyword/location, ~600+ full rewrites/day across
   3 portals), with cost growing roughly quadratically as the file grew. The dashboard
   also loaded the whole file into the browser and filtered client-side, which would
   crash the tab at scale before the rewrite cost even became the bottleneck. A lot
   changes between fixing this properly (SQLite, paginated queries) and the current
   code, which is the other reason this became its own phase rather than an in-place
   patch.

## Phase 2
The storage migration (CSV/XLSX → SQLite) referenced above addresses the scaling
limitation described above. It's used as a dev/QA stage to validate the new storage
approach before it's carried into Phase 3.

## Phase 3
Work moves on to Phase 3 (separate from this Phase 1 archive), built on what's
validated in Phase 2. Due to the removal of the original three portals' automation
from this codebase (see Limitations above) and the resulting portal swap, the
AI-powered features originally planned here — job matching, cover letter generation,
application assistance — move to Phase 3 instead, built against the new portal(s)
rather than this archive. The planned space-themed dashboard UI moves there too, due
to the UI complexity of reworking it alongside the portal swap.

## Requirements
Windows + Microsoft Edge (driver paths and CMD-launch flow are Windows-specific),
Python 3, `selenium`, `openpyxl`, `webdriver_manager`.

## Setup

### 1. `config.json`
Not committed (gitignored) — create it yourself at the project root:
```json
{
  "candidate": {
    "name": "Your Name",
    "role_keywords": ["Job Title 1", "Job Title 2"],
    "locations": ["City1", "City2"],
    "experience": "3",
    "experience_years": 3
  },
  "blacklist": ["senior", "lead", "internship", "..."],
  "settings": {
    "max_job_age_days": 7,
    "search_timeout_seconds": 30,
    "experience_levels": [1, 2, 3, 4]
  },
  "browser": {
    "edge_profile_path": "C:\\SeleniumEdgeProfile",
    "edge_profile_directory": "Default"
  }
}
```
`role_keywords` and `locations` drive every Counter/Scraper/Validator run; `blacklist`
is a title-substring filter checked by `scraper.is_blacklisted()` in addition to the
persistent `blacklist.xlsx`.

### 2. Edge / Selenium profile (dedicated, not your default profile)
Both scraping paths in this project run a **separate, dedicated Edge profile** —
never your everyday browser profile:
- `create_driver.py` → `C:\SeleniumEdgeProfile` (Portal B/Portal A — Selenium-launched directly).
- `portal_c_helpers.py` → `PORTAL_C_PROFILE_DIR = C:\SeleniumEdgeProfile` on its own
  debug port (Portal C — CMD-launched, see below).

**Why not your default profile:** Selenium itself needs `--remote-debugging-port`
enabled to control Edge. Starting with Edge 149 (version 149.0.4022.52, released to
the stable channel June 4, 2026), Edge no longer allows remote debugging on your
**default** profile/user-data-dir at all, for security reasons — it only accepts it
on a separate, dedicated `--user-data-dir` that sits outside the normal Edge profile
folder. That's why this dedicated profile exists in the first place — every portal's
driver needs it, not just Portal C.

The Portal C/Anti-bot flow (`antibot_helpers.py`) additionally relies on this same
dedicated, already-logged-in profile so Selenium can attach to an already-running
Edge window instead of launching its own automated one (which Anti-bot fingerprints
and blocks) — but the profile itself is required regardless, for Selenium to work
at all.

Steps to set it up once:
1. Create the profile folder: `C:\SeleniumEdgeProfile`.
2. Launch Edge pointed at it, with debugging enabled, and log in manually:
   ```
   "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" ^
     --remote-debugging-port=9222 ^
     --user-data-dir="C:\SeleniumEdgeProfile" --profile-directory=Default
   ```
3. In that window, log in to Portal A / Portal B / Portal C as normal and close it —
   the session cookies now live in this profile, so scrapers reuse your login instead
   of hitting a login wall every run.
4. `create_driver.sync_profile_data()` can additionally copy Cookies/Login
   Data/Local/Session Storage from your **real** Edge profile into this one on
   startup — see that function for the source path, which is hardcoded per-machine
   and needs updating for your own Windows username before use.
5. Confirm `config.json`'s `browser.edge_profile_path` matches the folder from step 1.

`portal_c_helpers.py` / `antibot_helpers.py` reuse the same profile+port pattern
(`PORTAL_C_PROFILE_DIR`, `PORTAL_C_DEBUG_PORT = 9222`) but launch/attach via CMD
(`subprocess.Popen`) rather than Selenium's own launcher, plus the Anti-bot-hang
recovery logic documented in `docs/antibot_helpers.py.md`.

## Rules — before committing
Check every file for machine-specific or personal values before pushing:
- [ ] No real Windows username in any path (e.g. `create_driver.py`'s `REAL_PROFILE` —
      use a `<User_account>` placeholder, not your actual folder).
- [ ] No personal candidate info committed — `config.json` is gitignored; if you ever
      add an example/template config, scrub `candidate.name` / `locations` /
      `role_keywords` to placeholders first.
- [ ] `user-agent` string in `create_driver.py` — the Chrome/Edge version number is
      pinned and will drift from your actual installed Edge version over time. Before
      each run (or at least periodically), check your real version at
      `edge://version` and update the `Chrome/...` / `Edg/...` numbers in the
      `--user-agent=` string to match — a mismatched UA is a stealth-detection risk,
      not just cosmetic.
- [ ] `EDGE_PATH` / `PORTAL_C_PROFILE_DIR` / `DEBUG_PORT` / `edge_profile_path` — confirm
      these still match your actual Edge install path and chosen profile folder.
- [ ] No API keys, tokens, or session cookies committed anywhere (this project doesn't
      use API keys currently, but check before adding any integration).
- [ ] Re-run the data-file check against `.gitignore` (see earlier in this doc) any
      time a new file gets added to the project root.

## Data files (not meant for version control)
`jobs.csv`, `scraper_jobs.xlsx`, `blacklist.csv` / `blacklist.xlsx`, `career_apps.csv`,
`search_state.json`, `workflows.json`, `logs/` — these are runtime data/logs, not code.
Recommended before pushing: add them to `.gitignore` rather than committing as-is.

## Future features
The features below were originally planned for this project but move to Phase 3
(see note above) — listed here for historical context only, not planned for this
Phase 1 archive:
- **AI-powered job matching** — use an LLM to score/filter postings against the profile instead of static rule-based eligibility checks.
- **AI-generated cover letters / resume tailoring** — auto-draft personalized cover letters and tailor resume content per posting.
- **AI application assistant** — summarize job descriptions and suggest which postings are worth prioritizing.
- **Space-themed dashboard UI** — redesign the dashboard with a space theme (dark starfield background, glowing accent colors, orbit/planet-style visuals for status indicators). Moves to Phase 3 due to UI complexity — reworking the existing dashboard's styling in place wasn't worth it alongside the portal swap, so it's being built fresh there instead.

## Disclaimer
This is a personal automation project. Automating interactions with third-party job
portals is subject to their terms of service — see [Limitations](#limitations--why-this-stopped)
above for why the scraping/automation code in this repo has been removed.

# Job-Hunter-Agent-Phase-1
Phase 1 archive of a job-hunting dashboard I built entirely by prompting Claude, with no programming background. Automated scraping was removed after hitting job portals' ToS restrictions — kept here as a documented, working local tool for tracking applications.