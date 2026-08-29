# workflow_tracker.py

**Role:** Stage reporter shared by all portal scrapers and the Counter — updates the live stage in `workflows.json` and appends to `logs/<WF_ID>.txt`.

## Functions
- `_get_wf_id()` — reads `WF_ID` env var.
- `_log(wf_id, message)` — appends a timestamped line to the workflow's log file.
- `_update_workflows_json(wf_id, stage)` — thread-safe update of the workflow's current stage.
- `make_location_code(location)` / `make_stage_code(portal, keyword, location)` — short codes used in stage labels/log tags.
- `update_stage(stage, keyword='', location='', portal='')` — the main call sites use to report progress.
- `log_info(message)` — general-purpose log line (no stage change).
- `get_config_path()` — resolves the active run's config file path.

## Depends on
`threading.Lock` (safe concurrent writes from subprocess)

## Used by
Nearly every scraper/counter/validator module: `scraper_portal_b.py`, `scraper_portal_a.py`, `job_counter.py`, `portal_b_helpers.py`, `blacklist_manager.py`, `tracker.py`, etc.
