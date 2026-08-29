# dashboard_scraper.py

**Role:** HTML/JS for the dashboard's Scraper tab (Request / Workflow / Log sub-tabs) — where the user configures and launches Counter/Scraper/Validator runs and watches live status.

## Functions
- `build_scraper_html()` — tab markup, including the status-symbol legend table built from `STATUS_LEGEND`.
- `build_scraper_js()` — client-side logic: submitting new requests, polling workflow status, rendering the log viewer.

## Depends on
`dashboard_ui` (esc), `dashboard_workflows` (STATUS_LEGEND)

## Used by
`dashboard_server.py`
