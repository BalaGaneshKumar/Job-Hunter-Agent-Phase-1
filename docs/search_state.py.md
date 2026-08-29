# search_state.py

**Role:** Pure JSON state management (no browser interaction) for scrape progress — backed by `search_state.json`. Tracks per-portal/keyword/location pagination position, completion flags, job counts, and runtime estimates so a scrape can pause/resume across runs.

## Functions
- `load_search_state()` / `save_search_state(state)` — file I/O with default-key backfill.
- `get_page` / `save_page` / `reset_portal` — pagination cursor.
- `mark_completed` / `is_completed` — completion flag per combo.
- `save_job_count` / `get_job_count` / `is_counted` / `reset_counter_flag` — Counter results cache.
- `reset_scraper_flag` — clears scrape-completed flag (e.g. to force a re-run).
- `get_total_runtime(portal)` — sums estimated runtime across combos for a portal.
- `save_job_to_state` / `get_saved_jobs` / `clear_saved_jobs` — an in-progress job buffer (survives a crash before the next flush).
- `get_total_pages(total_jobs, per_page=25)` / `estimate_runtime(total_jobs, seconds_per_job=45)` — small math helpers.

## Used by
`scraper_portal_b.py`, `scraper_portal_a.py`, `scraper_portal_c.py`, `job_counter.py`
