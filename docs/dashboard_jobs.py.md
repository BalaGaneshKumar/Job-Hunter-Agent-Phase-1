# dashboard_jobs.py

**Role:** HTML/JS for the dashboard's Jobs, Blacklist, and Profile tabs.

## Functions
- `build_jobs_html(cfg, kw_json, loc_json, bl_json, prof_json, locations)` — tab markup + filter controls (status, portal).
- `build_jobs_js(kw_json, loc_json, bl_json, prof_json)` — client-side logic: `reloadJobsCSV()` fetches the full `jobs.csv`/`blacklist.csv` as JSON, `parseCSV()` parses it, `renderJobs()` does **all** filtering/sorting/pagination in the browser (20 jobs/page).

## Depends on
`dashboard_ui` (esc, html_page), `dashboard_workflows` (load_config, read_file_text, read_profile, file paths)

## Used by
`dashboard_server.py`

## Phase 1 limitation / Phase 2 driver
This file loads the entire jobs/blacklist file into the browser and filters client-side. This is the main scalability wall flagged in `storage_migration_handoff.md` — at current size (~8,500 rows / 13MB) this risks crashing the browser tab before server-side rewrite cost even becomes the bottleneck. Phase 2 plan: server-side paginated/filtered queries against SQLite instead.
