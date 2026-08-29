# tracker.py

**Role:** Scraper-side Excel/CSV persistence — writes scraped jobs to `scraper_jobs.xlsx` and syncs them into the master `jobs.csv`.

## Functions
- `initialize_scraper_excel()` — creates `scraper_jobs.xlsx` with header if missing.
- `load_existing_jobs()` — loads current jobs (for dedup).
- `batch_write_jobs(jobs, filename=SCRAPER_FILE)` — appends a batch of scraped jobs to the xlsx.
- `sync_to_master()` — merges `scraper_jobs.xlsx` into `jobs.csv` (master record).
- `export_blacklist_csv()` — exports the blacklist to CSV form.
- `sanitize(value)` — strips illegal Excel characters (`ILLEGAL_CHARACTERS_RE`) before writing.

## Phase 1 limitation / Phase 2 driver
`sync_to_master()` / `batch_write_jobs()` / `export_blacklist_csv()` fire on **every page** of every scrape run, not once per run — a single keyword/location combo can be 30+ pages, so this is a full-file read+rewrite ~600+ times/day across 3 portals. Cost scales with current file size (`jobs.csv` already 13MB / ~8,500 rows), so it gets worse roughly quadratically as the file grows. This is the primary driver for the Phase 2 SQLite migration (see `storage_migration_handoff.md`).

## Used by
`scraper_portal_b.py`, `scraper_portal_a.py`, `scraper_portal_c.py`
