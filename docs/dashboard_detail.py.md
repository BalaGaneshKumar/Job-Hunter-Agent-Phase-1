# dashboard_detail.py

**Role:** Renders the single-workflow "detail" page (status, stage history, live log tail) shown when a user drills into one workflow from the dashboard.

## Functions
- `build_workflow_detail_html(wf_id)` — looks up the workflow via `get_workflow`, renders status/log HTML using the shared status legend/symbols.

## Depends on
`dashboard_ui` (esc, html_page), `dashboard_workflows` (get_workflow, read_workflow_log, status constants)

## Used by
`dashboard_server.py`

## Known issue
A bug was flagged in this file (not yet detailed) — see `storage_migration_handoff.md`, to be fixed independently of any storage migration.

## Phase 2 note
No CSV/xlsx dependency — only touches `workflows.json`/logs, so unaffected by the SQLite migration.
