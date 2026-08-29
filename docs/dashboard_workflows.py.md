# dashboard_workflows.py

**Role:** Core workflow engine — config I/O, `workflows.json` CRUD, the workflow queue, subprocess launching for Counter/Scraper/Validator, and log reading. The backbone `dashboard_server.py` and the tab modules build on.

## Key functions
- `load_config()` / `save_config()` — `config.json` I/O.
- `load_workflows()` / `save_workflows()` / `get_workflow()` / `update_workflow()` — `workflows.json` state.
- `generate_workflow_id()` / `create_workflow_record()` / `add_workflow_record()` — new workflow bookkeeping.
- `enqueue_request()` / `advance_queue()` / `get_running_workflow()` / `get_next_waiting_workflow()` / `clear_old_waiting_workflows()` — the single-workflow-at-a-time queue.
- `_compute_scraper_counter_planned_stages()` / `_compute_validator_planned_stages()` — precompute the expected stage list for progress display.
- `run_single_workflow(wf_id)` / `run_validator_workflow(wf_id)` — launch `python scraper.py` / `python job_counter.py` / `python validator.py` as a subprocess with `WF_ID`/`WF_PORTAL` env vars, monitor it.
- `kill_edge()` — force-kills any stray Edge/driver processes.
- `log_workflow()` / `read_workflow_log()` / `read_all_logs()` — per-workflow log file access.
- `read_file_text()` / `read_profile()` — misc file readers (e.g. resume/profile JSON).

## Depends on
`subprocess`, `threading`, `json`; lazily imports `selenium`/`validator.py`-adjacent modules only where needed.

## Used by
`dashboard_server.py` and effectively every other `dashboard_*.py` module.

## Phase 2 note
Config/workflow JSON I/O is unaffected by the SQLite migration; only the jobs/blacklist/career CSV paths (`JOBS_CSV`, `BLACKLIST_CSV` constants referenced elsewhere) are in scope.
