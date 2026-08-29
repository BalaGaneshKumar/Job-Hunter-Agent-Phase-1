# scraper.py

**Role:** Unified Scraper entry point (new — replaces the dashboard previously invoking `scraper_portal_b.py`/`scraper_portal_a.py`/`scraper_portal_c.py` directly). Launched as `python scraper.py` with `WF_ID`/`WF_PORTAL` env vars ('AL'/'NK'/'LI'/'IN').

## Functions
- `is_blacklisted(title, blacklist)` — checks a job title against the blacklist (shared logic, identical across all three portal scrapers).
- `format_duration(seconds)` — human-readable duration formatting.
- `print_progress(tag, start_time, jobs_found, total_expected)` — console progress line.
- `load_config()` — reads run config.
- `flush_jobs_to_excel(tag)` — writes buffered jobs out via `tracker.py`.
- `main()` — dispatches to `scraper_portal_b.run_portal_b_scraper()` / `scraper_portal_a.run_portal_a_scraper()` / `scraper_portal_c.run_portal_c_scraper()` based on `WF_PORTAL`.

## Mirrors
The `counter_*.py` / `validator_*.py` common+per-portal split.

## Launched by
`dashboard_workflows.py`'s `run_single_workflow()`.
