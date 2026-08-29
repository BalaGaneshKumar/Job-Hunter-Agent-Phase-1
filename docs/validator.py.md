# validator.py

**Role:** Job Link Validator — for every `jobs.csv` row with Status in `('Scraped', 'Eligible')` and a blank `Internal/External` column, opens the job URL and classifies it:
- expired-marker present → `Status = 'Ineligible'`
- internal apply-button → `Internal/External = 'Internal'`
- external apply-button → `Internal/External = 'External'`
- neither found → left untouched, logged as "Not defined" (retried automatically next run)

Launched by `dashboard_workflows.run_validator_sequence()` as `python validator.py` with `WF_ID`/`WF_PORTAL` env vars ('AL'/'NK'/'LI').

## Functions
- `staging_path(wf_id)` — per-run staging CSV path (crash-safety).
- `load_jobs(source_path=JOBS_CSV)` / `save_jobs(jobs_by_url, target_path=JOBS_CSV)` — full-file read/rewrite.
- `build_buckets(jobs_by_url, wf_portal, wf_locations=None)` — groups rows needing validation by portal.
- `wait_for_page(driver, timeout=8)` — page-load wait helper.
- `flush_and_cleanup(jobs_by_url, touched_urls, staging_csv)` — writes results back, clears staging.
- `main()` — orchestration loop.

## Portal-unique checks
Delegated to `validator_portal_b.py` / `validator_portal_a.py` / `validator_portal_c.py` (mirrors the `counter_*.py` split).

## Phase 2 note
`load_jobs`/`save_jobs` flagged for SQLite migration.
