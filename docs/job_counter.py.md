# job_counter.py

**Role:** Counter workflow entry point — estimates total job count per keyword/location/portal combo before a Scraper run, so runtime can be estimated and progress tracked.

## Functions
- `load_config()` — reads run config (keywords, locations, portal selection).
- `main()` — dispatches per portal using `WF_PORTAL` env var ('AL' = all three, or 'NK'/'LI'/'IN' for one), calling into `counter_portal_b.py` / `counter_portal_a.py` / `counter_portal_c.py`, saving results via `search_state.save_job_count`.

## Launched by
`dashboard_workflows.py` as `python job_counter.py` with `WF_ID`/`WF_PORTAL` env vars set.

## Depends on
`create_driver.py`, `search_state.py`, `workflow_tracker.py`, `portal_b_helpers.py`, `portal_c_helpers.py`, `antibot_helpers.py`, `counter_portal_b.py`, `counter_portal_a.py`, `counter_portal_c.py`
