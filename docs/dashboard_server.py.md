# dashboard_server.py

**Role:** Main dashboard entry point — a plain `http.server` app (no framework). Run with `python dashboard_server.py`, opens at `http://localhost:8080`.

## Functions
- `build_dashboard_html(active_tab='jobs', subtab=None)` — assembles the full page shell + active tab's HTML.
- `DashboardHandler(BaseHTTPRequestHandler)` — routes GET/POST requests: page loads, `/api/*` data endpoints (jobs/blacklist/profile CSV-as-JSON, workflow CRUD, career apps/sites, backup trigger, kill-edge).

## Depends on
All `dashboard_*.py` modules, `career_tracker.py`

## Phase 2 note
`/api/jobs-csv`, `/api/blacklist-csv` and the job-status/save endpoints are flagged to become paginated SQLite queries instead of full-file read/rewrite (see `storage_migration_handoff.md`).
