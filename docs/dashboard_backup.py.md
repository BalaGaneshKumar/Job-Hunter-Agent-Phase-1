# dashboard_backup.py

**Role:** "One Drive Uploader" — reads `jobs.csv` + `blacklist.csv` (+ career data) and writes a single styled `.xlsx` (one tab per status) into a local OneDrive-synced folder so OneDrive syncs it to the cloud automatically.

## Functions
- `_apply_grid_border` / `_autosize` / `_style_sheet` — openpyxl formatting helpers.
- `_read_csv(path)` — plain CSV reader.
- `run_onedrive_backup()` — orchestrates the full read → style → write flow. Only external entry point (called from `dashboard_server.py`'s backup button endpoint).

## Depends on
`openpyxl`, `dashboard_workflows` (paths), `career_tracker`

## Phase 2 note
Low-priority migration target — only triggered by a manual button, not part of the per-page rewrite bottleneck. Output stays `.xlsx` regardless of backend storage.
