# career_tracker.py

**Role:** CRUD for the separate "career applications" tracker (manual job-application log, distinct from the scraped `jobs.csv` pipeline), backed by `career_apps.csv` / `career_sites.csv`.

## Functions
- `load_career_apps()` / `load_career_sites()` — read the two CSVs into lists of dicts.
- `save_career_apps(rows)` / `save_career_sites(rows)` — full rewrite of the CSVs.

## Columns
- Apps: company, link, credential, credtype, passhint, role, location, date, stage, substage, ghostedsub, jobid, notes
- Sites: name, url, cred, notes

## Depends on
`workflow_tracker.log_info`

## Used by
`dashboard_server.py`, `dashboard_backup.py`, `dashboard_career.py` (UI)

## Phase 2 note
Low-priority candidate for SQLite migration (files are small: ~87KB/1.4KB).
